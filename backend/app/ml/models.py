import os
import json
import joblib
import numpy as np
from datetime import datetime, timezone
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest, RandomForestClassifier, GradientBoostingRegressor
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support, confusion_matrix,
    mean_absolute_error, root_mean_squared_error, r2_score
)
from app.ml.dataset_generator import generate_industrial_dataset, FAILURE_MODES, INDEX_TO_FAILURE_MODE
from app.ml.feature_extractor import FEATURE_NAMES

MODELS_DIR = "models/weights"

class IndustrialAnomalyDetector:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
        self.score_min = -0.5
        self.score_max = 0.5

    def fit(self, X_normal: np.ndarray):
        X_scaled = self.scaler.fit_transform(X_normal)
        self.model.fit(X_scaled)
        raw_scores = self.model.decision_function(X_scaled)
        self.score_min = float(np.min(raw_scores))
        self.score_max = float(np.max(raw_scores))

    def predict_score(self, X: np.ndarray) -> float:
        """Returns normalized anomaly score between 0.0 (normal) and 1.0 (highly anomalous)."""
        X_scaled = self.scaler.transform(X.reshape(1, -1))
        raw = float(self.model.decision_function(X_scaled)[0])
        # Invert and normalize decision function
        normalized = 1.0 - ((raw - self.score_min) / (self.score_max - self.score_min + 1e-6))
        return float(np.clip(normalized, 0.0, 1.0))

class IndustrialFaultClassifier:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = RandomForestClassifier(n_estimators=120, max_depth=12, random_state=42)

    def fit(self, X: np.ndarray, y: np.ndarray):
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)

    def predict(self, X: np.ndarray):
        X_scaled = self.scaler.transform(X.reshape(1, -1))
        probs = self.model.predict_proba(X_scaled)[0]
        class_idx = int(np.argmax(probs))
        class_name = INDEX_TO_FAILURE_MODE.get(class_idx, "NORMAL")
        confidence = float(probs[class_idx])
        return class_idx, class_name, confidence, probs

class IndustrialRULPredictor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
        self.residual_std: float = 4.5

    def fit(self, X: np.ndarray, y: np.ndarray):
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        preds = self.model.predict(X_scaled)
        self.residual_std = float(np.std(y - preds))

    def predict(self, X: np.ndarray):
        X_scaled = self.scaler.transform(X.reshape(1, -1))
        pred_rul = max(0.0, float(self.model.predict(X_scaled)[0]))
        # 90% Confidence bounds (1.645 * residual_std)
        ci_lower = max(0.0, pred_rul - (1.645 * self.residual_std))
        ci_upper = pred_rul + (1.645 * self.residual_std)
        return pred_rul, ci_lower, ci_upper

def train_and_cache_models():
    """Train all models on physics-grounded synthetic dataset and persist metrics."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    metrics_path = os.path.join(MODELS_DIR, "evaluation_metrics.json")
    
    print("[ML Pipeline] Generating physics degradation training data...")
    X, y_cls, y_rul = generate_industrial_dataset(samples_per_mode=200, window_size=10)

    # Train / Validation / Test split (70% / 15% / 15%)
    X_train, X_temp, y_cls_train, y_cls_temp, y_rul_train, y_rul_temp = train_test_split(
        X, y_cls, y_rul, test_size=0.30, random_state=42, stratify=y_cls
    )
    X_val, X_test, y_cls_val, y_cls_test, y_rul_val, y_rul_test = train_test_split(
        X_temp, y_cls_temp, y_rul_temp, test_size=0.50, random_state=42, stratify=y_cls_temp
    )

    print(f"[ML Pipeline] Train size: {len(X_train)}, Val size: {len(X_val)}, Test size: {len(X_test)}")

    # 1. Train Anomaly Detector (using Normal training samples)
    normal_mask = (y_cls_train == 0)
    X_normal = X_train[normal_mask]
    anomaly_detector = IndustrialAnomalyDetector()
    anomaly_detector.fit(X_normal)
    joblib.dump(anomaly_detector, os.path.join(MODELS_DIR, "anomaly_detector.joblib"))

    # Anomaly evaluation on test set (Normal vs All Faults)
    test_anomaly_scores = [anomaly_detector.predict_score(x) for x in X_test]
    test_is_anomaly = (y_cls_test != 0)
    pred_is_anomaly = np.array(test_anomaly_scores) > 0.55
    anom_acc = float(accuracy_score(test_is_anomaly, pred_is_anomaly))

    # 2. Train Fault Classifier
    fault_classifier = IndustrialFaultClassifier()
    fault_classifier.fit(X_train, y_cls_train)
    joblib.dump(fault_classifier, os.path.join(MODELS_DIR, "fault_classifier.joblib"))

    # Classifier evaluation
    X_test_scaled = fault_classifier.scaler.transform(X_test)
    y_cls_pred = fault_classifier.model.predict(X_test_scaled)
    cls_acc = float(accuracy_score(y_cls_test, y_cls_pred))
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(y_cls_test, y_cls_pred, average="macro", zero_division=0)
    conf_mat = confusion_matrix(y_cls_test, y_cls_pred).tolist()

    # 3. Train RUL Predictor
    rul_predictor = IndustrialRULPredictor()
    rul_predictor.fit(X_train, y_rul_train)
    joblib.dump(rul_predictor, os.path.join(MODELS_DIR, "rul_predictor.joblib"))

    # RUL evaluation
    X_test_rul_scaled = rul_predictor.scaler.transform(X_test)
    y_rul_pred = rul_predictor.model.predict(X_test_rul_scaled)
    rul_mae = float(mean_absolute_error(y_rul_test, y_rul_pred))
    rul_rmse = float(root_mean_squared_error(y_rul_test, y_rul_pred))
    rul_r2 = float(r2_score(y_rul_test, y_rul_pred))

    # Feature Importances
    importances = fault_classifier.model.feature_importances_
    feat_importance_dict = {name: float(imp) for name, imp in zip(FEATURE_NAMES, importances)}

    # Persist structured evaluation report
    metrics = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset_size": len(X),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "classes": FAILURE_MODES,
        "feature_count": len(FEATURE_NAMES),
        "classification": {
            "accuracy": round(cls_acc, 4),
            "precision_macro": round(float(p_macro), 4),
            "recall_macro": round(float(r_macro), 4),
            "f1_macro": round(float(f1_macro), 4),
            "confusion_matrix": conf_mat
        },
        "regression_rul": {
            "mae_hours": round(rul_mae, 2),
            "rmse_hours": round(rul_rmse, 2),
            "r2_score": round(rul_r2, 4)
        },
        "anomaly_detection": {
            "accuracy": round(anom_acc, 4),
            "threshold": 0.55
        },
        "feature_importances": feat_importance_dict
    }

    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"[ML Pipeline] Training complete! Classifier F1: {f1_macro:.4f}, RUL MAE: {rul_mae:.2f}h, Anomaly Acc: {anom_acc:.4f}")
    return metrics
