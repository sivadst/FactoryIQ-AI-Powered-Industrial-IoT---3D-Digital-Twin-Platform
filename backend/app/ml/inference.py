import os
import joblib
import numpy as np
from typing import List, Dict, Any, Optional
from app.ml.feature_extractor import extract_features_from_window
from app.ml.xai_rca import compute_local_xai_attribution, generate_rca_report
from app.ml.models import train_and_cache_models, MODELS_DIR

_anomaly_detector = None
_fault_classifier = None
_rul_predictor = None

def get_models():
    global _anomaly_detector, _fault_classifier, _rul_predictor
    if _anomaly_detector is None or _fault_classifier is None or _rul_predictor is None:
        ae_file = os.path.join(MODELS_DIR, "anomaly_detector.joblib")
        clf_file = os.path.join(MODELS_DIR, "fault_classifier.joblib")
        rul_file = os.path.join(MODELS_DIR, "rul_predictor.joblib")

        if not (os.path.exists(ae_file) and os.path.exists(clf_file) and os.path.exists(rul_file)):
            print("[Inference] Model weights not found. Training on physics dataset...")
            train_and_cache_models()

        _anomaly_detector = joblib.load(ae_file)
        _fault_classifier = joblib.load(clf_file)
        _rul_predictor = joblib.load(rul_file)
        print("[Inference] All ML models loaded into memory successfully.")

    return _anomaly_detector, _fault_classifier, _rul_predictor

def calculate_dynamic_risk_score(
    p_fail: float,
    anomaly_score: float,
    criticality: str = "High",
    rul_hours: float = 50.0
) -> float:
    """
    Calculate composite industrial risk index [0.0 - 100.0]:
    Risk = P(fail) * Impact(criticality) * Urgency(RUL) * AnomalyFactor
    """
    crit_weight = 1.0
    if criticality == "Critical":
        crit_weight = 1.25
    elif criticality == "High":
        crit_weight = 1.0
    elif criticality == "Medium":
        crit_weight = 0.75
    else:
        crit_weight = 0.5

    # Urgency factor rises exponentially as RUL drops below 48 hours
    if rul_hours <= 12.0:
        urgency = 1.3
    elif rul_hours <= 24.0:
        urgency = 1.15
    elif rul_hours <= 48.0:
        urgency = 1.0
    else:
        urgency = 0.7

    base_risk = (p_fail * 0.6 + anomaly_score * 0.4) * 100.0
    risk = base_risk * crit_weight * urgency
    return round(float(np.clip(risk, 0.0, 100.0)), 1)

def predict_machine_health(
    telemetry_window: List[Dict[str, Any]],
    criticality: str = "High"
) -> Dict[str, Any]:
    """
    Perform multi-model AI inference on 10-step telemetry window:
    - Anomaly Detection (Isolation Forest / Scaled Envelope)
    - Multi-Class Fault Classification (Random Forest / Tree)
    - RUL Prediction with 90% Confidence Interval
    - Explainable AI (XAI) Local Feature Importance
    - Root Cause Analysis (RCA) Diagnostic & Action
    - Industrial Risk Score
    """
    if not telemetry_window or len(telemetry_window) < 3:
        return {
            "anomaly_score": 0.05,
            "anomaly_status": "NORMAL",
            "predicted_failure": "NORMAL",
            "failure_probability": 0.02,
            "confidence": 0.98,
            "rul": 240.0,
            "rul_ci_lower": 210.0,
            "rul_ci_upper": 270.0,
            "risk_score": 5.0,
            "risk_level": "LOW",
            "top_drivers": [],
            "rca": None
        }

    anom_model, clf_model, rul_model = get_models()
    features = extract_features_from_window(telemetry_window)

    # 1. Anomaly Detection
    anomaly_score = anom_model.predict_score(features)
    if anomaly_score < 0.45:
        anomaly_status = "NORMAL"
    elif anomaly_score < 0.70:
        anomaly_status = "WARNING"
    elif anomaly_score < 0.85:
        anomaly_status = "ANOMALOUS"
    else:
        anomaly_status = "CRITICAL"

    # 2. Fault Classification
    class_idx, predicted_failure, confidence, probs = clf_model.predict(features)
    # Failure probability is probability of non-normal condition
    p_fail = float(1.0 - probs[0]) if len(probs) > 0 else 0.0

    # 3. RUL Prediction & Uncertainty
    rul_pred, rul_ci_lower, rul_ci_upper = rul_model.predict(features)

    # 4. Risk Scoring
    risk_score = calculate_dynamic_risk_score(p_fail, anomaly_score, criticality, rul_pred)
    if risk_score < 25.0:
        risk_level = "LOW"
    elif risk_score < 55.0:
        risk_level = "MEDIUM"
    elif risk_score < 80.0:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    # 5. Explainable AI (XAI) Local Drivers
    top_drivers = compute_local_xai_attribution(features, predicted_failure, anomaly_score)

    # 6. Root Cause Analysis (RCA)
    last_tick = telemetry_window[-1]
    health_score = float(last_tick.get("health_score", 95.0))
    rca = generate_rca_report(predicted_failure, anomaly_score, health_score, rul_pred, top_drivers)

    return {
        "anomaly_score": round(anomaly_score, 3),
        "anomaly_status": anomaly_status,
        "predicted_failure": predicted_failure,
        "failure_probability": round(p_fail, 3),
        "confidence": round(confidence, 3),
        "rul": round(rul_pred, 1),
        "rul_ci_lower": round(rul_ci_lower, 1),
        "rul_ci_upper": round(rul_ci_upper, 1),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "top_drivers": top_drivers,
        "rca": rca
    }
