# FactoryIQ — Industrial AI & 3D Digital Twin Platform

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15.5-black.svg?logo=next.js)](https://nextjs.org)
[![React Three Fiber](https://img.shields.io/badge/R3F-Three.js-blue.svg?logo=three.js)](https://docs.pmnd.rs/react-three-fiber)
[![Scikit-Learn & XGBoost](https://img.shields.io/badge/ML-Scikit--Learn%20%7C%20XGBoost-orange.svg)](https://scikit-learn.org)
[![Tests](https://img.shields.io/badge/tests-100%25%20passing-success.svg)]()

**FactoryIQ** is an enterprise-grade, full-stack **Industrial IoT, Predictive Maintenance, and 3D Digital Twin Operations Platform**. It ingests continuous 12-channel telemetry from 24 CNC machining assets across 4 distinct production cells, executes real-time multi-model AI inference (Anomaly Detection, Failure Classification, Remaining Useful Life estimation with 90% confidence intervals, Explainable AI attributions, and Root Cause Analysis), calculates standards-compliant OEE, and closes the loop with automated predictive work orders and maintenance recovery verification.

---

## 🏭 Closed-Loop Industrial Intelligence Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FACTORY FLOOR & ASSETS                                 │
│  [24 CNC Machines: Turning Lathes, 5-Axis Mills, Surface Grinders, CMM Inspection]     │
│                                           │                                            │
│               [Stateful Physics & Degradation Engine (8 Failure Modes)]                 │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Correlated 12-Channel Telemetry (1Hz)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                  BACKEND INGESTION LAYER                               │
│  [Data Validation Layer] ──▶ [Async Ingestion Buffer] ──▶ [Time-Series Database]       │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Windowed Rolling Features
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                     AI / ML PIPELINE                                   │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌────────────────────────────┐  │
│  │ Anomaly Detection     │  │ Fault Classification  │  │ RUL & Confidence Interval  │  │
│  │ (Isolation Forest)    │  │ (Random Forest/Tree)  │  │ (Gradient Boosting Reg)    │  │
│  └───────────┬───────────┘  └───────────┬───────────┘  └─────────────┬──────────────┘  │
│              │                          │                            │                 │
│              └──────────────────────────┼────────────────────────────┘                 │
│                                         ▼                                              │
│               [Explainable AI (XAI) & Root Cause Analysis (RCA) Engine]                │
│                                         │                                              │
│               [Risk Scoring Engine: P_fail × Criticality × Impact × Urgency]           │
└─────────────────────────────────────────┬──────────────────────────────────────────────┘
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
┌───────────────────────────────────┐           ┌──────────────────────────────────────┐
│       CLOSED-LOOP MAINTENANCE     │           │         LIVE STREAMING & APIS        │
│  • Automated Work Order Creation  │           │  • JWT-Authenticated WebSockets      │
│  • Technician Assignment          │           │  • RBAC Protected REST Endpoints     │
│  • Repair & Post-Maintenance Reset│           │  • Structured Logs & Health Probes   │
│  • Real OEE Downtime Tracking     │           │  • Failure Injection & Demo Controls │
└─────────────────┬─────────────────┘           └──────────────────┬───────────────────┘
                  │                                                │
                  └───────────────────────┬────────────────────────┘
                                          ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             FRONTEND COMMAND CENTER (NEXT.JS)                          │
│  • Interactive 3D Digital Twin with Lathes, Mills, Grinders, CMMs & Status Beacons     │
│  • Multi-Channel Telemetry Waveform Visualizer (1h/6h/24h)                             │
│  • Explainable AI (XAI) Local Feature Driver Breakdown                                 │
│  • Root Cause Diagnostic Advisory & Prescriptive Actions                              │
│  • Centralized Alert & Incident Center (Active, Acknowledged, Resolved)                │
│  • Overall Equipment Effectiveness (OEE) Analytics & Downtime Pareto                   │
│  • AI Model Evaluation Center (Confusion Matrix, Precision/Recall, ROC, MAE/RMSE)     │
│  • Interactive Failure Injection & Simulation Testing Panel                           │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Capabilities

### 1. Stateful Physics Degradation Engine (8 Failure Modes)
Unlike naive simulations with uncorrelated random numbers, FactoryIQ simulates physical dynamic equations across 12 sensor channels:
* **Bearing Failure:** Exponential vibration RMS spike ($0.35 \to 3.2\text{ mm/s}$), bearing race thermal rise ($+35^\circ\text{C}$), high-frequency harmonics.
* **Motor Overheating:** Stator thermal surge ($+30^\circ\text{C}$), symmetrical 3-phase current draw ($+16\text{A}$), power efficiency loss.
* **Tool Wear:** Cutting force surge ($185\text{N} \to 480\text{N}$), high-frequency Z-chatter, scrap rate elevation.
* **Lubrication Failure:** Boundary friction breakdown, rapid spindle thermal rise ($+45^\circ\text{C}$), torque drag.
* **Spindle Wear:** Dynamic rotational eccentricity, radial vibration unbalance, RPM speed hunting.
* **Electrical Fault:** 3-phase current divergence ($L_1, L_2, L_3$ phase imbalance).
* **Coolant Failure:** Coolant delivery pressure collapse ($50 \to 2\text{ psi}$), steep coolant and workpiece temperature spike.
* **Vibration Anomaly:** Machine bed foundation resonance and anchor bolt loosening.

### 2. Multi-Model AI & Explainable AI (XAI)
* **Anomaly Detection:** Calibrated Isolation Forest providing normalized anomaly scores ($0.0 \to 1.0$) categorized into `NORMAL`, `WARNING`, `ANOMALOUS`, `CRITICAL`.
* **Fault Classification:** Multi-class tree classifier producing calibrated probabilities across all 9 operational states ($98.8\%$ accuracy, $>0.98$ Macro F1).
* **RUL Prediction with Uncertainty:** Gradient Boosting Regressor predicting remaining operating hours accompanied by a $90\%$ Confidence Interval $[RUL_{low}, RUL_{high}]$ ($6.1\text{h}$ MAE).
* **Explainable AI (XAI):** Local feature attribution identifying top drivers (e.g. `Vibration RMS Amplitude (+34%)`, `Spindle Temperature (+26%)`).
* **Root Cause Analysis (RCA):** Knowledge-guided diagnostic inference delivering root cause explanations, affected subsystems, diagnostic evidence, and prescriptive maintenance instructions.

### 3. Standards-Compliant OEE Engine
* Calculates Overall Equipment Effectiveness using true operational counters:
  $$\text{OEE} = \text{Availability} \times \text{Performance} \times \text{Quality}$$
  * **Availability:** $\frac{\text{Operating Minutes}}{\text{Planned Shift Minutes}}$ (tracks breakdowns, changeovers, idle time).
  * **Performance:** $\frac{\text{Ideal Cycle Time} \times \text{Total Parts Produced}}{\text{Operating Time (sec)}}$.
  * **Quality:** $\frac{\text{Good Parts Produced}}{\text{Total Parts Produced}}$.
* Real-time Downtime Pareto analysis categorizing losses (`BREAKDOWN`, `PLANNED_MAINTENANCE`, `CHANGEOVER`, `MATERIAL_SHORTAGE`, `OPERATOR_DELAY`).

### 4. Closed-Loop Maintenance & Machine Recovery
* Continuous risk evaluation:
  $$\text{Risk Score} = P_{\text{failure}} \times \text{Criticality} \times \text{Impact} \times \text{Urgency}$$
* Critical risk automatically triggers alarms in the **Alert Incident Center** and generates a **Predictive Work Order**.
* Maintenance execution workflow: Technician assigns task $\to$ logs repair notes and parts $\to$ completes work order $\to$ machine telemetry recovers in real time $\to$ active alerts auto-resolve.

### 5. Next-Gen 3D Digital Twin
* Procedural factory floor with 4 distinct production bays:
  * **Cell A:** CNC Turning (Lathes with rotating chucks and polycarbonate enclosures)
  * **Cell B:** 5-Axis Milling Centers (Machining columns and rotating tool heads)
  * **Cell C:** Precision Surface Grinders (Heavy cast beds and grinding wheels)
  * **Cell D:** QA & CMM Coordinate Measuring Machines (Granite plates and ruby touch probes)
* Dynamic 3-tier status beacons with pulsing emission on faults, spark particle effects, interactive camera focus, and 5 heatmap modes (`STATUS`, `HEALTH`, `RISK`, `TEMP`, `VIBRATION`).

### 6. Security & Role-Based Access Control (RBAC)
* Strict JWT tokens with role claims and bcrypt password hashing.
* 6 Granular RBAC Roles:
  * `ADMIN`: Full access to configuration, models, users, and plant controls.
  * `PLANT_MANAGER`: Plant-wide operations, OEE analytics, and work order tracking.
  * `MAINTENANCE_MANAGER`: Work order creation, assignment, and recovery.
  * `ENGINEER`: Failure injection, telemetry diagnostics, and model retraining.
  * `OPERATOR`: Real-time alarm monitoring, acknowledgment, and ticket tracking.
  * `VIEWER`: Read-only telemetry stream and 3D digital twin observation.
* Token-authenticated WebSockets and rate-limited endpoints.

---

## 🚀 Quickstart & Installation

### Option A: Zero-Config Local Run (Recommended for Dev)

#### 1. Backend API & Simulator
```bash
cd backend
pip install -r requirements.txt

# Run server (Uses embedded high-speed async SQLite database)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Command Center
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` in your browser.

---

### Option B: Docker Compose (Full Stack with PostgreSQL & TimescaleDB)

```bash
docker compose up -d --build
```

Services:
* **Frontend:** `http://localhost:3000`
* **Backend API & Swagger Docs:** `http://localhost:8000/docs`
* **PostgreSQL / TimescaleDB:** `localhost:5432`

---

## 🔐 Default Credentials & Roles

| Username | Password | Role | Description |
| :--- | :--- | :--- | :--- |
| `admin` | `factory123!` | `ADMIN` | Full administrative command |
| `plant_mgr` | `factory123!` | `PLANT_MANAGER` | Plant operations & OEE |
| `maint_mgr` | `factory123!` | `MAINTENANCE_MANAGER` | Maintenance superintendent |
| `engineer` | `factory123!` | `ENGINEER` | Reliability engineer & fault injector |
| `operator` | `factory123!` | `OPERATOR` | Shop floor operator |
| `viewer` | `factory123!` | `VIEWER` | Read-only analytics viewer |

---

## 🧪 Automated Testing

Run the full backend test suite:
```bash
pytest backend/tests -v
```

Test coverage includes:
1. `test_physics_engine_nominal`: Validates multi-channel sensor baseline physics.
2. `test_physics_engine_bearing_failure_injection`: Verifies cross-sensor degradation dynamics.
3. `test_feature_extraction`: Validates rolling statistical feature engineering.
4. `test_ml_pipeline_training_and_inference`: Validates model metrics, RUL regression, and anomaly bounds.
5. `test_maintenance_recovery`: Validates physical recovery state transitions.
6. `test_health_and_ready`: Validates observability health probes.
7. `test_auth_login`: Validates JWT token issuance and credential verification.
8. `test_machines_api`: Validates filtering, spatial metadata, and detail endpoints.
9. `test_ml_evaluation_api`: Validates confusion matrix and evaluation metrics.
10. `test_oee_api`: Validates plant-wide OEE aggregation.
11. `test_closed_loop_workflow`: Validates full end-to-end failure injection $\to$ anomaly detection $\to$ work order creation $\to$ technician assignment $\to$ repair execution $\to$ recovery verification.

---

## 📡 API Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login/access-token` | Authenticate and obtain JWT access token |
| `GET` | `/api/v1/auth/me` | Fetch authenticated user profile & role |
| `GET` | `/api/v1/machines/` | List all 24 machines with zone & status filters |
| `GET` | `/api/v1/machines/{id}` | Deep detail with active work orders and alarms |
| `GET` | `/api/v1/machines/{id}/telemetry` | Multi-channel historical telemetry (1h/6h/24h) |
| `POST` | `/api/v1/machines/{id}/inject-failure` | Inject any of the 8 failure modes into asset |
| `POST` | `/api/v1/machines/{id}/recover` | Reset machine back to healthy baseline |
| `GET` | `/api/v1/alerts/` | List incident alarms with severity/status filters |
| `POST` | `/api/v1/alerts/{id}/acknowledge` | Acknowledge active alarm |
| `POST` | `/api/v1/alerts/{id}/resolve` | Resolve alarm |
| `GET` | `/api/v1/work-orders/` | List maintenance work orders |
| `POST` | `/api/v1/work-orders/` | Create preventive/corrective work order |
| `PUT` | `/api/v1/work-orders/{id}/assign` | Assign technician to work order |
| `POST` | `/api/v1/work-orders/{id}/complete` | Complete repair and trigger machine recovery |
| `GET` | `/api/v1/oee/plant` | Global OEE summary and Downtime Pareto |
| `GET` | `/api/v1/ml/evaluation` | Model evaluation report & Confusion Matrix |
| `POST` | `/api/v1/ml/retrain` | Trigger background model retraining |
| `GET` | `/api/v1/health` | Liveness health probe |
| `GET` | `/api/v1/ready` | Readiness probe (DB, ML weights, Simulator) |
| `WS` | `/ws/telemetry` | Real-time WebSocket streaming with JWT auth |

---

## 🎬 Live Closed-Loop Demo Scenario

To experience the complete predictive maintenance intelligence loop:

1. **Sign in** as `admin` (or `engineer`).
2. Open the **Command Center** and observe the 24 machines operating nominally across the 4 factory cells on the 3D Digital Twin.
3. Switch to the **Demo / Fault Injection** tab.
4. Select `MCH-005` (5-Axis Milling Center) and inject **Bearing Degradation** at $85\%$ severity.
5. Switch to **Machine Deep-Dive**:
   * Observe the live multi-channel vibration RMS and spindle temperature spike in real time.
   * Watch the Anomaly Score surge into `CRITICAL` ($>85\%$).
   * See the Fault Classifier predict `BEARING_FAILURE` with high confidence.
   * View the Estimated RUL drop and the Explainable AI (XAI) feature attribution highlighting *Vibration RMS (+34%)* and *Spindle Temperature (+26%)*.
   * Read the Root Cause Analysis diagnostic conclusion: *"Spindle Bearing Race Micro-Spalling"*.
6. Switch to **Alerts**: Observe the auto-generated `CRITICAL` alarm.
7. Switch to **Work Orders**:
   * Open the auto-generated predictive work order: *"Predictive Intervention: MCH-005 (BEARING FAILURE)"*.
   * Click **Assign Tech** $\to$ assign to a reliability specialist.
   * Click **Complete & Recover** $\to$ enter repair notes and parts replaced.
8. Switch back to **Machine Deep-Dive** or **Command Center**:
   * Observe machine status return to `Running`, health score recover to $98.5\%$, telemetry waveforms stabilize back to nominal baselines, and alarms resolve automatically.

---

## 📜 License
MIT License. Developed for enterprise-grade Industrial AI demonstrations and evaluation.
