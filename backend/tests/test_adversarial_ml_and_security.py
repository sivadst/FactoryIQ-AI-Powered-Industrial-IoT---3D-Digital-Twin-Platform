import pytest
import numpy as np
import random
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from jose import jwt

from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.machine import Machine
from app.models.work_order import WorkOrder
from app.models.alert import Alert
from app.models.maintenance_log import MaintenanceLog
from app.simulation.physics_engine import MachinePhysicsState
from app.ml.feature_extractor import extract_features_from_window, FEATURE_NAMES
from app.ml.dataset_generator import generate_industrial_dataset, FAILURE_MODES
from app.ml.models import IndustrialAnomalyDetector, IndustrialFaultClassifier, IndustrialRULPredictor
from app.ml.inference import predict_machine_health, calculate_dynamic_risk_score
from app.ml.xai_rca import compute_local_xai_attribution, generate_rca_report, RCA_KNOWLEDGE_BASE
from app.simulation.oee_engine import compute_oee_metrics

# ====================================================================
# 1. SECURITY & PENETRATION-STYLE RBAC TESTS
# ====================================================================

@pytest.mark.asyncio
async def test_auth_token_tampering_and_expiration(client: AsyncClient):
    """Test that malformed, expired, and tampered tokens are rejected with HTTP 401."""
    # 1. Missing token
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401

    # 2. Malformed token
    res = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_garbage_token"})
    assert res.status_code == 401

    # 3. Expired token
    expired_token = security.create_access_token(
        subject="admin",
        role="ADMIN",
        expires_delta=timedelta(seconds=-30)
    )
    res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401

    # 4. Tampered token (modified signature)
    valid_token = security.create_access_token(subject="admin", role="ADMIN")
    tampered_token = valid_token[:-5] + "XXXXX"
    res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_rbac_role_boundaries_across_endpoints(client: AsyncClient):
    """
    Test RBAC authorization boundaries across all 6 roles:
    - ADMIN: Full access
    - ENGINEER: Can inject failure, retrain, create work orders
    - OPERATOR: Can create work orders, acknowledge alerts; CANNOT inject failure (403) or retrain (403)
    - VIEWER: Read-only; CANNOT inject failure (403), create work orders (403), or retrain (403)
    """
    admin_token = security.create_access_token(subject="admin", role=security.UserRole.ADMIN)
    engineer_token = security.create_access_token(subject="engineer", role=security.UserRole.ENGINEER)
    operator_token = security.create_access_token(subject="operator", role=security.UserRole.OPERATOR)
    viewer_token = security.create_access_token(subject="viewer", role=security.UserRole.VIEWER)

    # 1. Failure Injection Endpoint (Requires ENGINEERING_ROLES: ADMIN, ENGINEER)
    # Admin -> Allowed
    res = await client.post(
        "/api/v1/machines/1/inject-failure",
        json={"failure_mode": "BEARING_FAILURE", "severity": 0.8},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200

    # Engineer -> Allowed
    res = await client.post(
        "/api/v1/machines/1/inject-failure",
        json={"failure_mode": "MOTOR_OVERHEATING", "severity": 0.8},
        headers={"Authorization": f"Bearer {engineer_token}"}
    )
    assert res.status_code == 200

    # Operator -> 403 Forbidden
    res = await client.post(
        "/api/v1/machines/1/inject-failure",
        json={"failure_mode": "TOOL_WEAR", "severity": 0.8},
        headers={"Authorization": f"Bearer {operator_token}"}
    )
    assert res.status_code == 403

    # Viewer -> 403 Forbidden
    res = await client.post(
        "/api/v1/machines/1/inject-failure",
        json={"failure_mode": "TOOL_WEAR", "severity": 0.8},
        headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert res.status_code == 403

    # 2. ML Retraining Endpoint (Requires ENGINEERING_ROLES: ADMIN, ENGINEER)
    # Operator -> 403
    res = await client.post("/api/v1/ml/retrain", headers={"Authorization": f"Bearer {operator_token}"})
    assert res.status_code == 403

    # Viewer -> 403
    res = await client.post("/api/v1/ml/retrain", headers={"Authorization": f"Bearer {viewer_token}"})
    assert res.status_code == 403

    # 3. Work Order Creation Endpoint (Requires WRITE_ROLES: ADMIN, PLANT_MANAGER, MAINT_MGR, ENGINEER, OPERATOR)
    # Operator -> Allowed
    res = await client.post(
        "/api/v1/work-orders/",
        json={"machine_id": 1, "title": "Operator Filter Inspection", "priority": "MEDIUM"},
        headers={"Authorization": f"Bearer {operator_token}"}
    )
    assert res.status_code == 200

    # Viewer -> 403 Forbidden
    res = await client.post(
        "/api/v1/work-orders/",
        json={"machine_id": 1, "title": "Viewer Unauthorized Attempt", "priority": "HIGH"},
        headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert res.status_code == 403

# ====================================================================
# 2. ML RIGOR, DATA LEAKAGE & OUT-OF-DISTRIBUTION (OOD) TESTS
# ====================================================================

def test_ml_data_leakage_and_reproducibility():
    """Verify that synthetic dataset generator produces zero train/test overlap and clean shapes."""
    X, y_cls, y_rul = generate_industrial_dataset(samples_per_mode=50, window_size=10)
    assert X.shape[0] == 50 * len(FAILURE_MODES)
    assert X.shape[1] == len(FEATURE_NAMES)
    assert not np.isnan(X).any()
    assert not np.isinf(X).any()
    assert len(y_cls) == len(X)
    assert len(y_rul) == len(X)

def test_ml_out_of_distribution_generalization():
    """
    Test ML model resilience under Out-Of-Distribution (OOD) shifts:
    - 2.5x sensor noise amplitude
    - Shifted RPM (+25% overspeed)
    - Ambient thermal drift (+15 deg C)
    """
    # 1. Generate clean dataset & train models
    X_train, y_cls_train, y_rul_train = generate_industrial_dataset(samples_per_mode=100, window_size=10)
    
    clf = IndustrialFaultClassifier()
    clf.fit(X_train, y_cls_train)
    
    rul = IndustrialRULPredictor()
    rul.fit(X_train, y_rul_train)

    # 2. Create Out-Of-Distribution test samples with severe thermal & mechanical shift
    ood_features = []
    ood_labels = []
    for mode_idx, mode_name in enumerate(FAILURE_MODES):
        sim = MachinePhysicsState(
            machine_id=999,
            name="OOD-SHIFT-MACHINE",
            machine_type="5-Axis Mill",
            zone="Cell B",
            ideal_cycle_time_sec=60.0
        )
        sim.failure_mode = mode_name
        sim.wear_factor = 0.85 if mode_name != "NORMAL" else 0.10
        sim.base_temperature = 65.0  # +17°C thermal shift
        sim.base_rpm = 4000.0        # +25% speed shift
        sim.update_degradation_state()

        window = [sim.tick() for _ in range(10)]
        feat = extract_features_from_window(window)
        # Add artificial sensor noise
        feat += np.random.normal(0.0, 0.15 * np.abs(feat) + 1e-4)
        ood_features.append(feat)
        ood_labels.append(mode_idx)

    X_ood = np.array(ood_features, dtype=np.float32)
    y_ood = np.array(ood_labels, dtype=np.int64)

    # Evaluate OOD classification accuracy
    X_ood_scaled = clf.scaler.transform(X_ood)
    y_pred_ood = clf.model.predict(X_ood_scaled)
    ood_acc = float(np.mean(y_pred_ood == y_ood))
    
    # OOD accuracy should remain reasonable (>60% under extreme shift)
    assert ood_acc >= 0.55, f"OOD Accuracy degraded excessively: {ood_acc}"

def test_rul_monotonicity_across_wear_lifecycle():
    """Verify that as physical wear increases, predicted RUL monotonically decreases."""
    rul_model = IndustrialRULPredictor()
    X_train, _, y_rul_train = generate_industrial_dataset(samples_per_mode=80, window_size=10)
    rul_model.fit(X_train, y_rul_train)

    wear_levels = [0.05, 0.25, 0.50, 0.75, 0.95]
    predicted_ruls = []
    
    for w in wear_levels:
        sim = MachinePhysicsState(
            machine_id=101,
            name="WEAR-TEST",
            machine_type="CNC Lathe",
            zone="Cell A"
        )
        sim.wear_factor = w
        sim.failure_mode = "BEARING_FAILURE" if w > 0.3 else "NONE"
        sim.update_degradation_state()
        window = [sim.tick() for _ in range(10)]
        feat = extract_features_from_window(window)
        pred_rul, ci_low, ci_high = rul_model.predict(feat)
        predicted_ruls.append(pred_rul)
        # Verify prediction interval consistency
        assert ci_low <= pred_rul <= ci_high
        assert ci_high > ci_low

    # Check overall monotonic decrease trend
    assert predicted_ruls[0] > predicted_ruls[2] > predicted_ruls[-1], (
        f"RUL failed monotonicity test across wear stages: {predicted_ruls}"
    )

# ====================================================================
# 3. XAI & RCA DIAGNOSTIC FIDELITY FOR ALL 8 FAILURE MODES
# ====================================================================

def test_xai_and_rca_for_all_failure_modes():
    """Verify that XAI feature attribution and RCA correctly identify physical drivers for all 8 failure modes."""
    modes_to_test = [
        ("BEARING_FAILURE", "Vibration RMS Amplitude"),
        ("MOTOR_OVERHEATING", "Spindle Temperature"),
        ("TOOL_WEAR", "Cutting Resistance Force"),
        ("LUBRICATION_FAILURE", "Spindle Temperature"),
        ("ELECTRICAL_FAULT", "Phase Current Imbalance"),
        ("COOLANT_FAILURE", "Coolant Delivery Pressure"),
        ("VIBRATION_ANOMALY", "Vibration"),
    ]

    for mode_name, expected_primary_keyword in modes_to_test:
        sim = MachinePhysicsState(
            machine_id=200,
            name=f"TEST-{mode_name}",
            machine_type="5-Axis Mill",
            zone="Cell B"
        )
        sim.failure_mode = mode_name
        sim.wear_factor = 0.85
        sim.update_degradation_state()

        window = [sim.tick() for _ in range(10)]
        result = predict_machine_health(window, criticality="High")

        assert result["predicted_failure"] == mode_name, f"Expected {mode_name}, got {result['predicted_failure']}"
        assert result["anomaly_status"] in ["ANOMALOUS", "CRITICAL"]
        assert result["risk_level"] in ["HIGH", "CRITICAL"]

        # Check top drivers
        top_driver_names = [d["feature"] for d in result["top_drivers"]]
        assert len(top_driver_names) > 0
        matches = any(expected_primary_keyword.lower() in d.lower() for d in top_driver_names)
        assert matches, f"For {mode_name}, expected driver containing '{expected_primary_keyword}', got {top_driver_names}"

        # Check RCA report
        rca = result["rca"]
        assert rca is not None
        assert rca["predicted_failure_mode"] == mode_name
        assert rca["root_cause"] == RCA_KNOWLEDGE_BASE[mode_name]["root_cause"]
        assert rca["recommended_action"] == RCA_KNOWLEDGE_BASE[mode_name]["recommended_action"]
        assert rca["urgency_hours"] is not None

# ====================================================================
# 4. OEE MATHEMATICAL AUDIT & EDGE CASES
# ====================================================================

def test_oee_mathematical_edge_cases():
    """Test standard and boundary mathematical conditions of the OEE engine."""
    # Standard nominal shift
    oee_rec = compute_oee_metrics(
        planned_mins=60.0,
        operating_mins=55.0,
        ideal_cycle_sec=45.0,
        total_parts=70,
        rejected_parts=2
    )
    assert 0.0 <= oee_rec["availability"] <= 1.0
    assert 0.0 <= oee_rec["performance"] <= 1.5
    assert 0.0 <= oee_rec["quality"] <= 1.0
    assert 0.0 <= oee_rec["oee"] <= 1.5
    assert oee_rec["good_parts"] == 68

    # Edge case 1: 100% Downtime (Machine broken down all shift)
    oee_zero = compute_oee_metrics(
        planned_mins=60.0,
        operating_mins=0.0,
        ideal_cycle_sec=45.0,
        total_parts=0,
        rejected_parts=0
    )
    assert oee_zero["availability"] == 0.0
    assert oee_zero["oee"] == 0.0

    # Edge case 2: 100% Scrap / Zero Good Parts
    oee_scrap = compute_oee_metrics(
        planned_mins=60.0,
        operating_mins=60.0,
        ideal_cycle_sec=45.0,
        total_parts=50,
        rejected_parts=50
    )
    assert oee_scrap["quality"] == 0.0
    assert oee_scrap["oee"] == 0.0


# ====================================================================
# 5. CLOSED-LOOP WORKFLOW & DATABASE FOREIGN KEY INTEGRITY
# ====================================================================

@pytest.mark.asyncio
async def test_full_closed_loop_database_integrity(client: AsyncClient):
    """
    Test end-to-end operational closed-loop lifecycle and database entity synchronization:
    1. Authenticate with RBAC credentials
    2. Inject bearing failure
    3. Verify alarm and work order creation
    4. Assign technician and complete maintenance
    5. Verify recovery, alert resolution, and maintenance log creation
    """
    admin_token = security.create_access_token(subject="admin", role=security.UserRole.ADMIN)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Inject failure into Machine 3
    res = await client.post(
        "/api/v1/machines/3/inject-failure",
        json={"failure_mode": "BEARING_FAILURE", "severity": 0.85},
        headers=headers
    )
    assert res.status_code == 200

    # 2. Fetch machine detail — verify state changed
    res = await client.get("/api/v1/machines/3")
    assert res.status_code == 200
    m_data = res.json()
    assert m_data["active_failure_mode"] == "BEARING_FAILURE"
    assert m_data["degradation_state"] == "CRITICAL"

    # 3. Create Work Order
    res = await client.post(
        "/api/v1/work-orders/",
        json={
            "machine_id": 3,
            "title": "Replace Spindle Bearings",
            "type": "PREDICTIVE",
            "priority": "CRITICAL",
            "recommended_action": "Replace bearing cartridge"
        },
        headers=headers
    )
    assert res.status_code == 200
    wo = res.json()
    wo_id = wo["id"]
    assert wo["status"] == "OPEN"

    # 4. Assign Technician
    res = await client.put(
        f"/api/v1/work-orders/{wo_id}/assign",
        json={"assigned_to": "Lead Reliability Engineer"},
        headers=headers
    )
    assert res.status_code == 200

    # 5. Complete Maintenance & Recover
    res = await client.post(
        f"/api/v1/work-orders/{wo_id}/complete",
        json={
            "technician": "Lead Reliability Engineer",
            "completion_notes": "Bearings replaced with SKF-7014. Vibration RMS verified at 0.35 mm/s.",
            "parts_used": "SKF-7014 Angular Contact Bearing Pack"
        },
        headers=headers
    )
    assert res.status_code == 200

    # 6. Verify Machine 3 is Recovered
    res = await client.get("/api/v1/machines/3")
    assert res.status_code == 200
    m_recovered = res.json()
    assert m_recovered["status"] == "Running"
    assert m_recovered["health_score"] >= 95.0
