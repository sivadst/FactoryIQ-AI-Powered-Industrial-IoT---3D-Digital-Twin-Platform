import asyncio
import json
from app.api.websockets.stream import manager
from app.ml.inference import predict_machine_health

# Dictionary to keep short window of telemetry per machine for inference
telemetry_windows = {}

async def broadcast_telemetry(telemetry_batch):
    message = {
        "type": "telemetry_batch",
        "data": []
    }
    for t in telemetry_batch:
        t_dict = {
            "machine_id": t.machine_id,
            "vibration_x": t.vibration_x,
            "vibration_y": t.vibration_y,
            "vibration_z": t.vibration_z,
            "temperature_spindle": t.temperature_spindle,
            "temperature_coolant": t.temperature_coolant,
            "current_l1": t.current_l1,
            "current_l2": t.current_l2,
            "current_l3": t.current_l3,
            "pressure_coolant": t.pressure_coolant,
            "pressure_air": t.pressure_air,
            "rpm_spindle": t.rpm_spindle,
            "cutting_force": t.cutting_force,
            "time": t.time.isoformat()
        }
        
        # Add to window for ML
        if t.machine_id not in telemetry_windows:
            telemetry_windows[t.machine_id] = []
        telemetry_windows[t.machine_id].append(t_dict)
        if len(telemetry_windows[t.machine_id]) > 10:
            telemetry_windows[t.machine_id] = telemetry_windows[t.machine_id][-10:]
            
        # Get ML Inference
        ml_results = predict_machine_health(telemetry_windows[t.machine_id])
        t_dict.update(ml_results)
        
        message["data"].append(t_dict)
    
    await manager.broadcast(message, 'all')
