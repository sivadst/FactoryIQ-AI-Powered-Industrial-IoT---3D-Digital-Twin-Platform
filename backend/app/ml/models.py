import torch
import torch.nn as nn
import numpy as np
import os
import xgboost as xgb
import pandas as pd
from app.ml.cmapss_downloader import download_and_extract_cmapss

# LSTM RUL Predictor
class RUL_LSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size):
        super(RUL_LSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out

# Autoencoder Anomaly Detector
class AnomalyAutoencoder(nn.Module):
    def __init__(self, input_dim):
        super(AnomalyAutoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 4)
        )
        self.decoder = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(),
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, input_dim)
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

def get_train_data(data_dir="data"):
    # Load CMAPSS mock data
    file_path = os.path.join(data_dir, "train_FD001.txt")
    columns = ['unit_number', 'time_in_cycles', 'setting_1', 'setting_2', 'setting_3'] + [f'sensor_{i}' for i in range(1, 22)]
    df = pd.read_csv(file_path, sep=' ', header=None, names=columns)
    
    # We use 12 sensors for our platform
    features = [f'sensor_{i}' for i in range(1, 13)]
    
    # Calculate RUL
    rul = pd.DataFrame(df.groupby('unit_number')['time_in_cycles'].max()).reset_index()
    rul.columns = ['unit_number', 'max']
    df = df.merge(rul, on=['unit_number'], how='left')
    df['RUL'] = df['max'] - df['time_in_cycles']
    df.drop('max', axis=1, inplace=True)
    
    return df[features].values, df['RUL'].values

def train_and_cache_models():
    models_dir = "models/weights"
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)

    download_and_extract_cmapss("data")
    X_train, y_train = get_train_data("data")
    
    # 1. Train LSTM (RUL)
    lstm_path = os.path.join(models_dir, "rul_lstm.pth")
    if not os.path.exists(lstm_path):
        print("Training LSTM for RUL prediction...")
        # Prepare sequences
        seq_length = 10
        X_seq = []
        y_seq = []
        for i in range(len(X_train) - seq_length):
            X_seq.append(X_train[i:i+seq_length])
            y_seq.append(y_train[i+seq_length-1])
        
        X_seq = torch.tensor(np.array(X_seq), dtype=torch.float32)
        y_seq = torch.tensor(np.array(y_seq), dtype=torch.float32).unsqueeze(1)
        
        model_lstm = RUL_LSTM(input_size=12, hidden_size=32, num_layers=2, output_size=1)
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model_lstm.parameters(), lr=0.01)
        
        # Train for a few epochs
        for epoch in range(5):
            optimizer.zero_grad()
            outputs = model_lstm(X_seq)
            loss = criterion(outputs, y_seq)
            loss.backward()
            optimizer.step()
        
        torch.save(model_lstm.state_dict(), lstm_path)
        print("LSTM trained and saved.")

    # 2. Train Autoencoder
    ae_path = os.path.join(models_dir, "anomaly_ae.pth")
    if not os.path.exists(ae_path):
        print("Training Autoencoder for Anomaly Detection...")
        X_tensor = torch.tensor(X_train, dtype=torch.float32)
        model_ae = AnomalyAutoencoder(input_dim=12)
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model_ae.parameters(), lr=0.01)
        
        for epoch in range(5):
            optimizer.zero_grad()
            outputs = model_ae(X_tensor)
            loss = criterion(outputs, X_tensor)
            loss.backward()
            optimizer.step()
            
        torch.save(model_ae.state_dict(), ae_path)
        print("Autoencoder trained and saved.")

    # 3. Train XGBoost Classifier
    xgb_path = os.path.join(models_dir, "fault_xgb.json")
    if not os.path.exists(xgb_path):
        print("Training XGBoost Classifier...")
        # Mock fault classes: 0 (Normal), 1 (Bearing), 2 (Spindle), 3 (Coolant)
        y_cls = np.random.randint(0, 4, size=len(X_train))
        model_xgb = xgb.XGBClassifier(objective='multi:softmax', num_class=4)
        model_xgb.fit(X_train, y_cls)
        model_xgb.save_model(xgb_path)
        print("XGBoost trained and saved.")

if __name__ == "__main__":
    train_and_cache_models()
