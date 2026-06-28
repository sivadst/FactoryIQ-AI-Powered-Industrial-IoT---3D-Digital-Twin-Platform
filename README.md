# FactoryIQ

FactoryIQ is a production-grade industrial IoT platform that ingests synthetic time-series sensor data from a simulated CNC machining factory, predicts equipment failures 48 hours in advance, tracks OEE, and visualizes the live factory floor in a 3D digital twin.

## Features
- **3D Digital Twin:** Procedurally generated 200-machine factory floor using React Three Fiber.
- **Sensor Streaming:** FastAPI WebSockets stream 12 sensor channels per machine at 1Hz.
- **Predictive Maintenance (AI):** PyTorch LSTM for Remaining Useful Life (RUL), PyTorch Autoencoder for Anomaly Detection, XGBoost for Fault Classification (trained on mock CMAPSS data).
- **OEE & Work Orders:** Automated Overall Equipment Effectiveness calculations and ticket generation.
- **PostgreSQL & TimescaleDB:** High-performance time-series database.

## Quickstart

### Prerequisites
- Docker & Docker Compose
- Node.js >= 18
- Python >= 3.10

### 1. Database
```bash
docker compose up -d db
```

### 2. Backend API & Simulator
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Frontend Dashboard
```bash
cd frontend
npm install
npm run build
npm run serve
```

Visit `http://localhost:3000` to view the command center.
