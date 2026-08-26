import pytest
import numpy as np
from app.simulation.physics_engine import MachinePhysicsState
from app.ml.feature_extractor import extract_features_from_window, FEATURE_NAMES
from app.ml.inference import predict_machine_health, calculate_dynamic_risk_score
from app.ml.models import train_and_cache_models
from app.ml.xai_rca import compute_local_xai_attribution, generate_rca_report

def test_physics_engine_nominal():
    state = MachinePhysicsState(1, "MCH-001", "CNC Lathe", "Cell A")
    tick = state.tick()
    assert tick["machine_id"] == 1
    assert 0.1 <= tick["vibration_x"] <= 1.5
    assert 30.0 <= tick["temperature_spindle"] <= 85.0
    assert tick["degradation_state"] == "HEALTHY"

def test_physics_engine_bearing_failure_injection():
    state = MachinePhysicsState(2, "MCH-002", "5-Axis Mill", "Cell B")
    state.inject_failure("BEARING_FAILURE", severity=0.85)
    
    # Tick several times
    for _ in range(5):
        tick = state.tick()

    assert state.failure_mode == "BEARING_FAILURE"
    assert state.degradation_state in ("ANOMALOUS", "CRITICAL")
    assert tick["vibration_x"] > 1.0  # Spike in vibration
    assert tick["temperature_spindle"] > 60.0  # Spindle thermal rise

def test_feature_extraction():
    state = MachinePhysicsState(3, "MCH-003", "Surface Grinder", "Cell C")
    window = [state.tick() for _ in range(10)]
    features = extract_features_from_window(window)
    
    assert len(features) == len(FEATURE_NAMES)
    assert not np.isnan(features).any()
    assert features[3] > 0.0  # vib_rms

def test_ml_pipeline_training_and_inference():
    metrics = train_and_cache_models()
    assert metrics["classification"]["f1_macro"] > 0.70
    assert metrics["regression_rul"]["mae_hours"] < 40.0
    assert metrics["anomaly_detection"]["accuracy"] > 0.70

    # Test inference on degraded window
    state = MachinePhysicsState(4, "MCH-004", "CNC Lathe", "Cell A")
    state.inject_failure("BEARING_FAILURE", severity=0.85)
    window = [state.tick() for _ in range(10)]
    
    results = predict_machine_health(window, criticality="Critical")
    assert results["anomaly_score"] > 0.40
    assert results["risk_score"] > 30.0
    assert len(results["top_drivers"]) > 0
    assert results["rca"] is not None
    assert results["rca"]["predicted_failure_mode"] in ("BEARING_FAILURE", "MOTOR_OVERHEATING", "LUBRICATION_FAILURE")

def test_maintenance_recovery():
    state = MachinePhysicsState(5, "MCH-005", "5-Axis Mill", "Cell B")
    state.inject_failure("MOTOR_OVERHEATING", severity=0.90)
    assert state.failure_mode == "MOTOR_OVERHEATING"
    
    # Execute maintenance
    state.execute_maintenance()
    assert state.failure_mode == "NONE"
    assert state.degradation_state == "RECOVERED"
    assert state.health_score > 90.0
