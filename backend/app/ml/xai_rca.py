from typing import List, Dict, Any
import numpy as np
from app.ml.feature_extractor import FEATURE_NAMES

RCA_KNOWLEDGE_BASE = {
    "BEARING_FAILURE": {
        "root_cause": "Spindle Bearing Race Micro-Spalling & Rolling Element Fatigue",
        "subsystem": "Main Spindle & Angular Contact Bearing Pack",
        "severity": "CRITICAL",
        "evidence_template": "High-frequency vibration harmonic surge combined with localized spindle bearing thermal rise.",
        "recommended_action": "Inspect spindle bearing assembly within 8 hours. Measure radial runout and check lubrication viscosity. Replace bearing cartridge if clearance exceeds 0.04mm."
    },
    "MOTOR_OVERHEATING": {
        "root_cause": "Stator Winding Thermal Overload & Impaired Heat Dissipation",
        "subsystem": "Spindle Drive Motor & Fan Housing",
        "severity": "HIGH",
        "evidence_template": "Elevated winding temperatures accompanied by elevated symmetrical 3-phase current draw.",
        "recommended_action": "Inspect motor cooling airflow, clean heat sink fins, check drive inverter current limits, and measure stator resistance."
    },
    "TOOL_WEAR": {
        "root_cause": "Cutting Edge Flank Wear & Carbide Coating Micro-Chipping",
        "subsystem": "Tool Turret / Milling Spindle Tooling",
        "severity": "MEDIUM",
        "evidence_template": "Elevated dynamic cutting force combined with high-frequency Z-axis cutting chatter.",
        "recommended_action": "Index or replace cutting insert on active tool station. Verify workpiece surface roughness and tool geometry offsets."
    },
    "LUBRICATION_FAILURE": {
        "root_cause": "Hydrodynamic Lubricant Starvation & Friction Breakdown",
        "subsystem": "Centralized Automatic Lubrication System",
        "severity": "CRITICAL",
        "evidence_template": "Rapid spindle temperature rise combined with increased mechanical torque resistance.",
        "recommended_action": "Check lubrication reservoir level, inspect metering valves, clear clogged delivery lines, and verify pump pressure."
    },
    "SPINDLE_WEAR": {
        "root_cause": "Spindle Journal Eccentricity & Mechanical Unbalance",
        "subsystem": "Spindle Rotor & Belt/Direct Coupling",
        "severity": "HIGH",
        "evidence_template": "Radial vibration runout with spindle speed hunting and rotational jitter.",
        "recommended_action": "Perform dynamic spindle balancing. Inspect coupling elastomer and check collet clamping tension."
    },
    "ELECTRICAL_FAULT": {
        "root_cause": "Phase Current Imbalance & Inverter Gate Drive Fault",
        "subsystem": "Variable Frequency Drive (VFD) & Power Infeed",
        "severity": "CRITICAL",
        "evidence_template": "Significant current phase divergence between L1, L2, and L3.",
        "recommended_action": "De-energize drive enclosure. Measure phase-to-ground isolation and inspect VFD IGBT gate firing circuits."
    },
    "COOLANT_FAILURE": {
        "root_cause": "Through-Spindle Coolant Pump Cavitation / Flow Obstruction",
        "subsystem": "High-Pressure Coolant Delivery Circuit",
        "severity": "HIGH",
        "evidence_template": "Coolant line pressure drop accompanied by steep coolant and workpiece temperature spikes.",
        "recommended_action": "Clean coolant suction intake filters, inspect pressure relief valve, and check coolant tank concentration."
    },
    "VIBRATION_ANOMALY": {
        "root_cause": "Structural Machine Bed Resonance & Loose Anchor Fasteners",
        "subsystem": "Cast Iron Base & Machine Foundation Mounts",
        "severity": "MEDIUM",
        "evidence_template": "Broadband structural vibration amplification across primary axis.",
        "recommended_action": "Torque foundation anchor bolts, inspect leveling pads, and check for loose sheet metal enclosures."
    },
    "NORMAL": {
        "root_cause": "Equipment Operating Within Baseline Parameters",
        "subsystem": "All Systems Nominal",
        "severity": "LOW",
        "evidence_template": "All vibration, temperature, current, and pressure channels within 6-sigma process limits.",
        "recommended_action": "Continue standard autonomous maintenance shift inspections."
    }
}

FEATURE_DISPLAY_NAMES = {
    'vib_x_mean': 'Vibration X-Axis',
    'vib_y_mean': 'Vibration Y-Axis',
    'vib_z_mean': 'Vibration Z-Axis',
    'vib_rms': 'Vibration RMS Amplitude',
    'vib_kurtosis': 'Vibration Impact Kurtosis',
    'vib_crest_factor': 'Vibration Crest Factor',
    'temp_spindle_mean': 'Spindle Temperature',
    'temp_spindle_slope': 'Spindle Temp Rise Rate',
    'temp_coolant_mean': 'Coolant Temperature',
    'temp_delta': 'Spindle-Coolant Delta T',
    'current_mean': 'Motor Current Draw',
    'current_imbalance': 'Phase Current Imbalance',
    'current_slope': 'Current Load Gradient',
    'pressure_coolant_mean': 'Coolant Delivery Pressure',
    'pressure_air_mean': 'Pneumatic System Pressure',
    'rpm_mean': 'Spindle Rotational Speed',
    'rpm_std': 'Spindle Speed Stability',
    'force_mean': 'Cutting Resistance Force',
    'force_std': 'Cutting Dynamic Chatter',
    'operating_hours': 'Cumulative Machine Operating Age'
}

def compute_local_xai_attribution(
    features: np.ndarray,
    predicted_mode: str,
    anomaly_score: float
) -> List[Dict[str, Any]]:
    """
    Compute localized explainable AI (XAI) feature importance drivers for the current prediction.
    """
    if predicted_mode == "NORMAL" and anomaly_score < 0.45:
        return [
            {"feature": "Process Stability Index", "contribution": 94, "status": "NOMINAL"},
            {"feature": "Vibration Baseline", "contribution": 92, "status": "NOMINAL"},
            {"feature": "Thermal Equilibrium", "contribution": 91, "status": "NOMINAL"},
        ]

    # Calculate deviation from baseline nominals
    nominal_baseline = np.array([
        0.35, 0.35, 0.35, 0.60, 3.0, 2.5,
        48.0, 0.0, 23.5, 24.5,
        14.5, 0.4, 0.0,
        48.0, 90.0,
        3200.0, 15.0,
        185.0, 15.0,
        1500.0
    ], dtype=np.float32)

    deviations = np.abs(features - nominal_baseline) / (np.abs(nominal_baseline) + 1e-4)
    
    # Weight key diagnostic features depending on failure mode
    mode_weights = np.ones(len(FEATURE_NAMES), dtype=np.float32)
    if predicted_mode == "BEARING_FAILURE":
        mode_weights[3] *= 4.0  # vib_rms
        mode_weights[6] *= 3.0  # temp_spindle
        mode_weights[4] *= 2.5  # kurtosis
    elif predicted_mode == "MOTOR_OVERHEATING":
        mode_weights[6] *= 3.5  # temp_spindle
        mode_weights[10] *= 3.0  # current_mean
    elif predicted_mode == "TOOL_WEAR":
        mode_weights[17] *= 4.0  # force_mean
        mode_weights[2] *= 3.0  # vib_z
    elif predicted_mode == "LUBRICATION_FAILURE":
        mode_weights[6] *= 4.0  # temp_spindle
        mode_weights[10] *= 2.5  # current_mean
    elif predicted_mode == "ELECTRICAL_FAULT":
        mode_weights[11] *= 5.0  # current_imbalance
    elif predicted_mode == "COOLANT_FAILURE":
        mode_weights[13] *= 5.0  # pressure_coolant
        mode_weights[8] *= 3.0  # temp_coolant

    weighted_scores = deviations * mode_weights
    total_score = np.sum(weighted_scores) + 1e-6
    contributions = (weighted_scores / total_score) * 100.0

    # Sort descending
    top_indices = np.argsort(contributions)[::-1][:5]
    
    top_drivers = []
    for idx in top_indices:
        raw_name = FEATURE_NAMES[idx]
        disp_name = FEATURE_DISPLAY_NAMES.get(raw_name, raw_name)
        top_drivers.append({
            "feature": disp_name,
            "contribution": round(float(contributions[idx]), 1),
            "status": "ELEVATED" if contributions[idx] > 15.0 else "MODERATE"
        })
        
    return top_drivers

def generate_rca_report(
    predicted_mode: str,
    anomaly_score: float,
    health_score: float,
    rul_hours: float,
    top_drivers: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate comprehensive Root Cause Analysis (RCA) and Prescriptive Maintenance advisory.
    """
    kb = RCA_KNOWLEDGE_BASE.get(predicted_mode, RCA_KNOWLEDGE_BASE["NORMAL"])
    
    top_driver_names = [d["feature"] for d in top_drivers[:3]]
    driver_summary = ", ".join(top_driver_names) if top_driver_names else "Nominal operation"

    return {
        "predicted_failure_mode": predicted_mode,
        "root_cause": kb["root_cause"],
        "affected_subsystem": kb["subsystem"],
        "severity": kb["severity"],
        "evidence": f"{kb['evidence_template']} (Primary drivers: {driver_summary})",
        "recommended_action": kb["recommended_action"],
        "urgency_hours": round(max(1.0, min(rul_hours * 0.4, 24.0)), 1) if predicted_mode != "NORMAL" else None
    }
