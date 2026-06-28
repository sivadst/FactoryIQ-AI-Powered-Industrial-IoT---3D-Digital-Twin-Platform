import torch
import xgboost as xgb
import numpy as np
import os
from app.ml.models import RUL_LSTM, AnomalyAutoencoder

# Load cached models at startup to avoid retraining
models_dir = "models/weights"

# LSTM
rul_model = RUL_LSTM(input_size=12, hidden_size=32, num_layers=2, output_size=1)
if os.path.exists(os.path.join(models_dir, "rul_lstm.pth")):
    rul_model.load_state_dict(torch.load(os.path.join(models_dir, "rul_lstm.pth")))
rul_model.eval()

# Autoencoder
ae_model = AnomalyAutoencoder(input_dim=12)
if os.path.exists(os.path.join(models_dir, "anomaly_ae.pth")):
    ae_model.load_state_dict(torch.load(os.path.join(models_dir, "anomaly_ae.pth")))
ae_model.eval()

# XGBoost
xgb_model = xgb.XGBClassifier()
if os.path.exists(os.path.join(models_dir, "fault_xgb.json")):
    xgb_model.load_model(os.path.join(models_dir, "fault_xgb.json"))

def predict_machine_health(telemetry_window):
    """
    Takes a list of dicts (telemetry for the last N seconds)
    Returns RUL, Anomaly Score, and Fault Class.
    """
    if not telemetry_window or len(telemetry_window) < 10:
        return {"rul": None, "anomaly_score": None, "fault_class": None}
        
    # Extract features (the 12 sensors)
    features = ['vibration_x', 'vibration_y', 'vibration_z', 'temperature_spindle',
                'temperature_coolant', 'current_l1', 'current_l2', 'current_l3',
                'pressure_coolant', 'pressure_air', 'rpm_spindle', 'cutting_force']
                
    # Normalize briefly based on mock CMAPSS stats (approximate)
    data = []
    for t in telemetry_window[-10:]:
        row = [t[f] for f in features]
        data.append(row)
        
    X_seq = torch.tensor([data], dtype=torch.float32)
    X_latest = torch.tensor([data[-1]], dtype=torch.float32)
    X_xgb = np.array([data[-1]])
    
    # RUL Prediction
    with torch.no_grad():
        rul_pred = rul_model(X_seq).item()
        
    # Anomaly Detection (Reconstruction Error)
    with torch.no_grad():
        reconstructed = ae_model(X_latest)
        mse_loss = torch.nn.functional.mse_loss(reconstructed, X_latest).item()
        
    # Fault Classification
    fault_class = int(xgb_model.predict(X_xgb)[0])
    
    return {
        "rul": max(0, rul_pred),
        "anomaly_score": mse_loss,
        "fault_class": fault_class
    }
