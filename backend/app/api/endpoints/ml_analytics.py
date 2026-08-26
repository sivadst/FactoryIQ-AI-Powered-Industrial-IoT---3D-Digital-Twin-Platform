import os
import json
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from app.ml.models import train_and_cache_models, MODELS_DIR
from app.core import security

router = APIRouter()

@router.get("/evaluation")
def get_ml_evaluation_metrics():
    """
    Return comprehensive evaluation report computed on validation/test datasets:
    - Classification Accuracy, Macro Precision, Recall, F1
    - 9-Class Confusion Matrix
    - RUL Regression MAE, RMSE, R2 Score
    - Anomaly Detection Accuracy & Thresholds
    - Global Feature Importances
    """
    metrics_path = os.path.join(MODELS_DIR, "evaluation_metrics.json")
    if not os.path.exists(metrics_path):
        metrics = train_and_cache_models()
        return metrics

    try:
        with open(metrics_path, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read evaluation metrics: {e}")

@router.post("/retrain")
def retrain_models(
    background_tasks: BackgroundTasks,
    user_payload: security.TokenPayload = Depends(security.require_roles(security.UserRole.ENGINEERING_ROLES))
):
    """Trigger background model retraining on current physics dataset."""
    background_tasks.add_task(train_and_cache_models)
    return {"status": "SUCCESS", "message": f"ML retraining pipeline launched by {user_payload.sub}."}

