import numpy as np
import pandas as pd
import random
from typing import Tuple, List, Dict
from app.simulation.physics_engine import MachinePhysicsState
from app.ml.feature_extractor import extract_features_from_window, FEATURE_NAMES

FAILURE_MODES = [
    "NORMAL",
    "BEARING_FAILURE",
    "MOTOR_OVERHEATING",
    "TOOL_WEAR",
    "LUBRICATION_FAILURE",
    "SPINDLE_WEAR",
    "ELECTRICAL_FAULT",
    "COOLANT_FAILURE",
    "VIBRATION_ANOMALY"
]

FAILURE_MODE_MAP = {mode: idx for idx, mode in enumerate(FAILURE_MODES)}
INDEX_TO_FAILURE_MODE = {idx: mode for idx, mode in enumerate(FAILURE_MODES)}

def generate_industrial_dataset(
    samples_per_mode: int = 250,
    window_size: int = 10
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate a deterministic, physics-based dataset for training Anomaly Detection,
    Fault Classification, and RUL Prediction.
    
    Returns:
        X: Feature matrix of shape (N, num_features)
        y_cls: Class labels array of shape (N,)
        y_rul: Remaining Useful Life target in hours of shape (N,)
    """
    np.random.seed(42)
    random.seed(42)
    
    features_list: List[np.ndarray] = []
    labels_cls: List[int] = []
    labels_rul: List[float] = []

    machine_types = ["CNC Lathe", "5-Axis Mill", "Surface Grinder", "CMM Inspection"]

    for mode_idx, mode_name in enumerate(FAILURE_MODES):
        for sample_i in range(samples_per_mode):
            m_type = machine_types[sample_i % len(machine_types)]
            sim = MachinePhysicsState(
                machine_id=sample_i + 1,
                name=f"SIM-{sample_i:03d}",
                machine_type=m_type,
                zone="Cell A",
                ideal_cycle_time_sec=45.0
            )

            # Assign wear and degradation profile
            if mode_name == "NORMAL":
                sim.wear_factor = random.uniform(0.01, 0.20)
                sim.failure_mode = "NONE"
                target_rul = random.uniform(180.0, 350.0)
            else:
                sim.wear_factor = random.uniform(0.35, 0.95)
                sim.failure_mode = mode_name
                # Physics-grounded RUL inversely proportional to wear factor
                target_rul = max(2.0, (1.0 - sim.wear_factor) * 90.0 + random.gauss(0.0, 3.0))

            sim.update_degradation_state()

            # Generate a time window of sensor ticks
            window: List[Dict[str, Any]] = []
            for _ in range(window_size):
                tick_data = sim.tick()
                window.append(tick_data)

            feat = extract_features_from_window(window)
            features_list.append(feat)
            labels_cls.append(mode_idx)
            labels_rul.append(target_rul)

    X = np.array(features_list, dtype=np.float32)
    y_cls = np.array(labels_cls, dtype=np.int64)
    y_rul = np.array(labels_rul, dtype=np.float32)

    return X, y_cls, y_rul
