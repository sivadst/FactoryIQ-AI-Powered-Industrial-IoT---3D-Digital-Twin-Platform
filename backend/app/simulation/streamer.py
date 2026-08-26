import asyncio
from typing import List, Dict, Any
from app.api.websockets.stream import manager
from app.ml.inference import predict_machine_health

# Telemetry rolling window buffer per machine (10 time-steps)
telemetry_windows: Dict[int, List[Dict[str, Any]]] = {}

async def broadcast_telemetry(telemetry_batch: List[Dict[str, Any]]):
    """
    Attach real-time ML inference (Anomaly, Classification, RUL, XAI, RCA)
    and broadcast rich telemetry payload to WebSocket subscribers.
    """
    message = {
        "type": "telemetry_batch",
        "timestamp": telemetry_batch[0]["time"].isoformat() if telemetry_batch else None,
        "data": []
    }
    
    for t in telemetry_batch:
        m_id = t["machine_id"]
        
        # Maintain 10-step rolling window for ML
        if m_id not in telemetry_windows:
            telemetry_windows[m_id] = []
        telemetry_windows[m_id].append(t)
        if len(telemetry_windows[m_id]) > 10:
            telemetry_windows[m_id] = telemetry_windows[m_id][-10:]

        # Run AI/ML inference pipeline
        ml_results = predict_machine_health(telemetry_windows[m_id], criticality="High")
        
        t_dict = dict(t)
        t_dict["time"] = t["time"].isoformat() if hasattr(t["time"], "isoformat") else str(t["time"])
        t_dict.update(ml_results)
        
        message["data"].append(t_dict)

    await manager.broadcast(message, 'all')
