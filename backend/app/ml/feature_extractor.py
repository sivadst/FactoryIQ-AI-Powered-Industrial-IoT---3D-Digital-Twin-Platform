import numpy as np
from typing import List, Dict, Any

SENSOR_FEATURES = [
    'vibration_x', 'vibration_y', 'vibration_z', 'temperature_spindle',
    'temperature_coolant', 'current_l1', 'current_l2', 'current_l3',
    'pressure_coolant', 'pressure_air', 'rpm_spindle', 'cutting_force'
]

FEATURE_NAMES = [
    'vib_x_mean', 'vib_y_mean', 'vib_z_mean', 'vib_rms', 'vib_kurtosis', 'vib_crest_factor',
    'temp_spindle_mean', 'temp_spindle_slope', 'temp_coolant_mean', 'temp_delta',
    'current_mean', 'current_imbalance', 'current_slope',
    'pressure_coolant_mean', 'pressure_air_mean',
    'rpm_mean', 'rpm_std',
    'force_mean', 'force_std',
    'operating_hours'
]

def extract_features_from_window(window: List[Dict[str, Any]]) -> np.ndarray:
    """
    Extract physics-derived rolling statistical features from a time window (e.g. 10 time-steps).
    Returns 1D numpy array of engineered features.
    """
    if not window:
        return np.zeros(len(FEATURE_NAMES), dtype=np.float32)

    # Convert sensor records to numpy array (T, 12)
    matrix = np.zeros((len(window), len(SENSOR_FEATURES)), dtype=np.float32)
    for i, t in enumerate(window):
        for j, f in enumerate(SENSOR_FEATURES):
            matrix[i, j] = float(t.get(f, 0.0))

    # Vibration calculations
    vx, vy, vz = matrix[:, 0], matrix[:, 1], matrix[:, 2]
    vib_x_mean = float(np.mean(vx))
    vib_y_mean = float(np.mean(vy))
    vib_z_mean = float(np.mean(vz))
    
    # 3-Axis Vibration RMS
    vib_mag = np.sqrt(vx**2 + vy**2 + vz**2)
    vib_rms = float(np.sqrt(np.mean(vib_mag**2)))
    
    # Kurtosis & Crest Factor
    vib_std = float(np.std(vib_mag)) + 1e-6
    vib_kurtosis = float(np.mean(((vib_mag - np.mean(vib_mag)) / vib_std) ** 4))
    vib_crest_factor = float(np.max(np.abs(vib_mag)) / (vib_rms + 1e-6))

    # Temperature calculations
    t_spindle = matrix[:, 3]
    t_coolant = matrix[:, 4]
    temp_spindle_mean = float(np.mean(t_spindle))
    temp_spindle_slope = float(t_spindle[-1] - t_spindle[0]) if len(t_spindle) > 1 else 0.0
    temp_coolant_mean = float(np.mean(t_coolant))
    temp_delta = float(temp_spindle_mean - temp_coolant_mean)

    # 3-Phase Current calculations
    i1, i2, i3 = matrix[:, 5], matrix[:, 6], matrix[:, 7]
    current_mean = float(np.mean((i1 + i2 + i3) / 3.0))
    current_imbalance = float(np.max(np.abs([
        np.mean(i1) - np.mean(i2),
        np.mean(i2) - np.mean(i3),
        np.mean(i3) - np.mean(i1)
    ])))
    current_slope = float(np.mean(i1[-1] + i2[-1] + i3[-1]) - np.mean(i1[0] + i2[0] + i3[0])) if len(i1) > 1 else 0.0

    # Pressure & Speed
    p_coolant = matrix[:, 8]
    p_air = matrix[:, 9]
    rpm = matrix[:, 10]
    force = matrix[:, 11]

    pressure_coolant_mean = float(np.mean(p_coolant))
    pressure_air_mean = float(np.mean(p_air))
    
    rpm_mean = float(np.mean(rpm))
    rpm_std = float(np.std(rpm))
    
    force_mean = float(np.mean(force))
    force_std = float(np.std(force))

    operating_hours = float(window[-1].get("operating_hours", 1200.0))

    features = np.array([
        vib_x_mean, vib_y_mean, vib_z_mean, vib_rms, vib_kurtosis, vib_crest_factor,
        temp_spindle_mean, temp_spindle_slope, temp_coolant_mean, temp_delta,
        current_mean, current_imbalance, current_slope,
        pressure_coolant_mean, pressure_air_mean,
        rpm_mean, rpm_std,
        force_mean, force_std,
        operating_hours
    ], dtype=np.float32)

    return features
