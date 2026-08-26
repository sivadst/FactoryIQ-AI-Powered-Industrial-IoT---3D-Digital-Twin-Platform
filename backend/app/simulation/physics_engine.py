import math
import random
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class MachinePhysicsState:
    def __init__(
        self,
        machine_id: int,
        name: str,
        machine_type: str,
        zone: str,
        criticality: str = "High",
        ideal_cycle_time_sec: float = 45.0
    ):
        self.machine_id = machine_id
        self.name = name
        self.machine_type = machine_type
        self.zone = zone
        self.criticality = criticality
        self.ideal_cycle_time_sec = ideal_cycle_time_sec
        
        self.status = "Running"  # Running, Idle, Fault, Maintenance
        self.degradation_state = "HEALTHY"  # HEALTHY, NORMAL_WEAR, EARLY_DEGRADATION, DEGRADING, ANOMALOUS, CRITICAL, FAILED, UNDER_MAINTENANCE, RECOVERED
        self.failure_mode = "NONE"  # NONE, BEARING_FAILURE, MOTOR_OVERHEATING, TOOL_WEAR, LUBRICATION_FAILURE, SPINDLE_WEAR, ELECTRICAL_FAULT, COOLANT_FAILURE, VIBRATION_ANOMALY
        
        # Continuous state parameters
        self.wear_factor: float = random.uniform(0.02, 0.08)  # 0.0 (pristine) to 1.0 (failed)
        self.wear_velocity: float = random.uniform(0.0001, 0.0004)  # baseline natural wear rate
        self.operating_hours: float = random.uniform(850.0, 3200.0)
        self.health_score: float = 100.0 - (self.wear_factor * 25.0)
        
        # Thermal & dynamics state
        self.thermal_inertia: float = 0.0
        self.tick_count: int = 0
        
        # Production counters for real OEE
        self.shift_planned_minutes: float = 60.0
        self.shift_operating_minutes: float = 58.0
        self.shift_downtime_minutes: float = 2.0
        self.shift_total_parts: int = 72
        self.shift_good_parts: int = 71
        self.shift_reject_parts: int = 1
        self.last_downtime_reason: str = "NONE"

    def inject_failure(self, failure_mode: str, severity: float = 0.6):
        """Manually or deterministically inject a specific failure mode."""
        self.failure_mode = failure_mode
        self.wear_factor = max(self.wear_factor, severity)
        self.wear_velocity = 0.015  # Rapid progression under active fault
        self.update_degradation_state()

    def execute_maintenance(self, technician: str = "Reliability Tech", notes: str = "Completed scheduled rebuild"):
        """Perform maintenance and reset machine back to recovered/healthy state."""
        self.status = "Running"
        self.degradation_state = "RECOVERED"
        self.failure_mode = "NONE"
        self.wear_factor = random.uniform(0.01, 0.04)
        self.wear_velocity = random.uniform(0.0001, 0.0003)
        self.health_score = 98.5
        self.shift_downtime_minutes = 0.0
        self.last_downtime_reason = "NONE"

    def update_degradation_state(self):
        """Update machine degradation state based on wear factor."""
        if self.status == "Maintenance":
            self.degradation_state = "UNDER_MAINTENANCE"
            self.health_score = 40.0
            return

        if self.wear_factor < 0.15:
            self.degradation_state = "HEALTHY"
            self.health_score = round(100.0 - (self.wear_factor * 20.0), 1)
        elif self.wear_factor < 0.35:
            self.degradation_state = "NORMAL_WEAR"
            self.health_score = round(95.0 - (self.wear_factor * 30.0), 1)
        elif self.wear_factor < 0.55:
            self.degradation_state = "EARLY_DEGRADATION"
            self.health_score = round(85.0 - (self.wear_factor * 35.0), 1)
        elif self.wear_factor < 0.75:
            self.degradation_state = "DEGRADING"
            self.health_score = round(70.0 - (self.wear_factor * 40.0), 1)
        elif self.wear_factor < 0.88:
            self.degradation_state = "ANOMALOUS"
            self.health_score = round(50.0 - (self.wear_factor * 40.0), 1)
        elif self.wear_factor < 0.96:
            self.degradation_state = "CRITICAL"
            self.health_score = round(30.0 - (self.wear_factor * 20.0), 1)
        else:
            self.degradation_state = "FAILED"
            self.status = "Fault"
            self.health_score = round(max(5.0, 15.0 - (self.wear_factor * 10.0)), 1)
            self.last_downtime_reason = "BREAKDOWN"

    def tick(self) -> Dict[str, Any]:
        """Compute one physics-correlated telemetry time-step for this machine."""
        self.tick_count += 1
        now = datetime.now(timezone.utc)
        
        # Advance operating hours and natural wear if running
        if self.status == "Running":
            self.operating_hours += (1.0 / 3600.0)
            self.wear_factor = min(1.0, self.wear_factor + self.wear_velocity)
            self.update_degradation_state()
            
            # Increment production counts
            if self.tick_count % max(1, int(self.ideal_cycle_time_sec)) == 0:
                self.shift_total_parts += 1
                # Reject chance increases with wear and tool failure
                reject_prob = 0.01 + (0.35 if self.failure_mode == "TOOL_WEAR" else self.wear_factor * 0.08)
                if random.random() < reject_prob:
                    self.shift_reject_parts += 1
                else:
                    self.shift_good_parts += 1

        w = self.wear_factor
        mode = self.failure_mode
        t_phase = self.tick_count * 0.1

        # =========================================================================
        # 1. Spindle RPM & Dynamic Speed
        # =========================================================================
        nominal_rpm = 3600.0 if "Mill" in self.machine_type else 2800.0 if "Lathe" in self.machine_type else 4200.0
        if self.status == "Running":
            rpm_jitter = random.gauss(0.0, 15.0)
            if mode in ("SPINDLE_WEAR", "BEARING_FAILURE"):
                rpm_jitter += math.sin(t_phase * 2.0) * (80.0 * w) + random.gauss(0.0, 40.0 * w)
            rpm_spindle = max(0.0, nominal_rpm + rpm_jitter)
        elif self.status == "Idle":
            rpm_spindle = 0.0
        else:
            rpm_spindle = 0.0

        # =========================================================================
        # 2. Vibration (X, Y, Z) with Harmonic Peaks
        # =========================================================================
        base_vib = 0.35 if self.status == "Running" else 0.05
        vib_noise_x = random.gauss(0.0, 0.04)
        vib_noise_y = random.gauss(0.0, 0.04)
        vib_noise_z = random.gauss(0.0, 0.03)

        if self.status == "Running":
            # Natural wear vibration progression
            vibration_x = base_vib + (w * 0.8) + vib_noise_x
            vibration_y = base_vib + (w * 0.7) + vib_noise_y
            vibration_z = base_vib + (w * 0.6) + vib_noise_z

            # Failure Mode Signatures
            if mode == "BEARING_FAILURE":
                # Severe exponential vibration harmonics
                bearing_spike = (math.sin(t_phase * 4.5) ** 2) * (2.8 * w) + (w ** 2 * 3.5)
                vibration_x += bearing_spike
                vibration_y += bearing_spike * 0.85
                vibration_z += bearing_spike * 0.65
            elif mode == "SPINDLE_WEAR":
                # Radial imbalance
                vibration_x += math.sin(t_phase) * (2.2 * w)
                vibration_y += math.cos(t_phase) * (2.0 * w)
            elif mode == "TOOL_WEAR":
                # High frequency cutting vibration in Z
                vibration_z += math.sin(t_phase * 8.0) * (1.9 * w) + (w * 1.4)
            elif mode == "VIBRATION_ANOMALY":
                # Resonance spike
                vibration_x += 2.4 * w
                vibration_y += 1.8 * w
        else:
            vibration_x = 0.02 + abs(vib_noise_x * 0.1)
            vibration_y = 0.02 + abs(vib_noise_y * 0.1)
            vibration_z = 0.01 + abs(vib_noise_z * 0.1)

        # =========================================================================
        # 3. Temperatures (Spindle & Coolant)
        # =========================================================================
        ambient_temp = 23.5
        if self.status == "Running":
            base_spindle_temp = 48.0 + (w * 12.0)
            if mode == "BEARING_FAILURE":
                base_spindle_temp += (38.0 * w)
            elif mode == "LUBRICATION_FAILURE":
                base_spindle_temp += (45.0 * w)
            elif mode == "MOTOR_OVERHEATING":
                base_spindle_temp += (30.0 * w)
            elif mode == "COOLANT_FAILURE":
                base_spindle_temp += (50.0 * w)
            
            temperature_spindle = base_spindle_temp + random.gauss(0.0, 0.8)
            
            # Coolant temperature
            base_coolant_temp = 24.0 + (w * 4.0)
            if mode == "COOLANT_FAILURE":
                base_coolant_temp += (36.0 * w)
            elif mode in ("BEARING_FAILURE", "MOTOR_OVERHEATING"):
                base_coolant_temp += (10.0 * w)
            temperature_coolant = base_coolant_temp + random.gauss(0.0, 0.4)
        else:
            temperature_spindle = ambient_temp + random.gauss(0.0, 0.2)
            temperature_coolant = ambient_temp - 1.5 + random.gauss(0.0, 0.2)

        # =========================================================================
        # 4. Three-Phase Electrical Currents (L1, L2, L3)
        # =========================================================================
        if self.status == "Running":
            nominal_current = 14.5 + (w * 3.0)
            
            # Additional drag increases current
            if mode in ("BEARING_FAILURE", "LUBRICATION_FAILURE"):
                nominal_current += (9.0 * w)
            elif mode == "MOTOR_OVERHEATING":
                nominal_current += (16.0 * w)

            cur_noise1 = random.gauss(0.0, 0.3)
            cur_noise2 = random.gauss(0.0, 0.3)
            cur_noise3 = random.gauss(0.0, 0.3)

            if mode == "ELECTRICAL_FAULT":
                # Distinct phase imbalance
                current_l1 = nominal_current + (18.0 * w) + cur_noise1
                current_l2 = nominal_current - (6.0 * w) + cur_noise2
                current_l3 = nominal_current - (5.0 * w) + cur_noise3
            else:
                current_l1 = nominal_current + cur_noise1
                current_l2 = nominal_current + cur_noise2
                current_l3 = nominal_current + cur_noise3
        else:
            current_l1 = 0.5 + abs(random.gauss(0.0, 0.05))
            current_l2 = 0.5 + abs(random.gauss(0.0, 0.05))
            current_l3 = 0.5 + abs(random.gauss(0.0, 0.05))

        # =========================================================================
        # 5. Coolant & Air Pressures
        # =========================================================================
        if self.status == "Running":
            base_coolant_p = 50.0 - (w * 5.0)
            if mode == "COOLANT_FAILURE":
                base_coolant_p = max(2.0, 50.0 - (48.0 * w))
            pressure_coolant = max(0.0, base_coolant_p + random.gauss(0.0, 1.2))
        else:
            pressure_coolant = 0.0
            
        pressure_air = 90.0 + random.gauss(0.0, 0.8)

        # =========================================================================
        # 6. Cutting Force (N)
        # =========================================================================
        if self.status == "Running":
            base_force = 185.0 + (w * 40.0)
            if mode == "TOOL_WEAR":
                base_force += (280.0 * w)
            elif mode == "SPINDLE_WEAR":
                base_force += (70.0 * w)
            cutting_force = max(0.0, base_force + random.gauss(0.0, 12.0))
        else:
            cutting_force = 0.0

        return {
            "machine_id": self.machine_id,
            "name": self.name,
            "machine_type": self.machine_type,
            "zone": self.zone,
            "status": self.status,
            "degradation_state": self.degradation_state,
            "failure_mode": self.failure_mode,
            "health_score": round(self.health_score, 1),
            "wear_factor": round(self.wear_factor, 4),
            "operating_hours": round(self.operating_hours, 2),
            "time": now,
            
            # 12 Sensor Channels
            "vibration_x": round(float(vibration_x), 3),
            "vibration_y": round(float(vibration_y), 3),
            "vibration_z": round(float(vibration_z), 3),
            "temperature_spindle": round(float(temperature_spindle), 2),
            "temperature_coolant": round(float(temperature_coolant), 2),
            "current_l1": round(float(current_l1), 2),
            "current_l2": round(float(current_l2), 2),
            "current_l3": round(float(current_l3), 2),
            "pressure_coolant": round(float(pressure_coolant), 2),
            "pressure_air": round(float(pressure_air), 2),
            "rpm_spindle": round(float(rpm_spindle), 1),
            "cutting_force": round(float(cutting_force), 1)
        }
