import os
from fastapi import APIRouter, status, Response
from sqlalchemy.future import select
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.simulation.factory_simulator import simulator
from app.ml.models import MODELS_DIR

router = APIRouter()

@router.get("/health")
def health_check():
    """Liveness probe: confirms process is alive."""
    return {"status": "HEALTHY", "service": "factoryiq-backend"}

@router.get("/ready")
async def readiness_check(response: Response):
    """Readiness probe: validates database connectivity, simulator, and ML model availability."""
    db_ok = False
    ml_ok = False
    sim_ok = len(simulator.physics_states) > 0 or simulator.is_running
    
    # 1. Check DB
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        db_ok = False

    # 2. Check ML weights
    ae_file = os.path.join(MODELS_DIR, "anomaly_detector.joblib")
    clf_file = os.path.join(MODELS_DIR, "fault_classifier.joblib")
    rul_file = os.path.join(MODELS_DIR, "rul_predictor.joblib")
    ml_ok = os.path.exists(ae_file) and os.path.exists(clf_file) and os.path.exists(rul_file)

    ready = db_ok and ml_ok and sim_ok

    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "ready": ready,
        "database": "CONNECTED" if db_ok else "DISCONNECTED",
        "ml_models": "LOADED" if ml_ok else "NOT_FOUND",
        "simulator": "INITIALIZED" if sim_ok else "STOPPED"
    }
