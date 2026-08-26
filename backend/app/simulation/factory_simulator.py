import asyncio
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy.future import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.session import AsyncSessionLocal
from app.models.machine import Machine
from app.models.telemetry import Telemetry
from app.simulation.physics_engine import MachinePhysicsState
from app.simulation.streamer import broadcast_telemetry
from app.core.config import settings

def validate_telemetry_packet(t: Dict[str, Any]) -> bool:
    """
    Data Quality Validation Layer:
    Rejects or cleans telemetry with missing values, physical impossibilities,
    or invalid sensor spikes.
    """
    try:
        # Check impossible physics values
        if t["vibration_x"] < 0 or t["vibration_x"] > 25.0: return False
        if t["temperature_spindle"] < -10.0 or t["temperature_spindle"] > 200.0: return False
        if t["current_l1"] < 0 or t["current_l1"] > 200.0: return False
        if t["pressure_coolant"] < 0 or t["pressure_coolant"] > 250.0: return False
        if t["rpm_spindle"] < 0 or t["rpm_spindle"] > 25000.0: return False
        return True
    except Exception:
        return False

class FactorySimulator:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.physics_states: Dict[int, MachinePhysicsState] = {}
        self.is_running = False

    async def initialize(self):
        """Load machines from database and initialize their physics simulators."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Machine))
            machines = result.scalars().all()
            
            for m in machines:
                state = MachinePhysicsState(
                    machine_id=m.id,
                    name=m.name,
                    machine_type=m.type,
                    zone=m.zone,
                    criticality=m.criticality,
                    ideal_cycle_time_sec=m.ideal_cycle_time_sec or 45.0
                )
                state.status = m.status
                state.degradation_state = m.degradation_state
                state.failure_mode = m.active_failure_mode
                state.health_score = m.health_score
                state.operating_hours = m.operating_hours
                
                # Align wear factor with initial state
                if m.degradation_state == "HEALTHY":
                    state.wear_factor = 0.05
                elif m.degradation_state == "ANOMALOUS":
                    state.wear_factor = 0.80
                elif m.degradation_state == "CRITICAL":
                    state.wear_factor = 0.92
                    
                self.physics_states[m.id] = state

            print(f"[Factory Simulator] Initialized physics states for {len(self.physics_states)} machines.")

    def inject_failure(self, machine_id: int, failure_mode: str, severity: float = 0.65) -> bool:
        """Inject specific failure mode into simulated machine."""
        if machine_id in self.physics_states:
            state = self.physics_states[machine_id]
            state.inject_failure(failure_mode, severity)
            print(f"[Factory Simulator] Injected {failure_mode} on {state.name} (ID: {machine_id})")
            return True
        return False

    def recover_machine(self, machine_id: int) -> bool:
        """Perform simulated maintenance recovery on machine."""
        if machine_id in self.physics_states:
            state = self.physics_states[machine_id]
            state.execute_maintenance()
            print(f"[Factory Simulator] Recovered machine {state.name} (ID: {machine_id})")
            return True
        return False

    async def simulation_tick(self):
        """Simulate one second across all factory machines, validate, store and broadcast."""
        try:
            telemetry_batch: List[Dict[str, Any]] = []
            db_records: List[Telemetry] = []
            
            for m_id, state in self.physics_states.items():
                tick_data = state.tick()
                
                if validate_telemetry_packet(tick_data):
                    telemetry_batch.append(tick_data)
                    
                    # Create DB model record
                    t_record = Telemetry(
                        time=tick_data["time"],
                        machine_id=m_id,
                        vibration_x=tick_data["vibration_x"],
                        vibration_y=tick_data["vibration_y"],
                        vibration_z=tick_data["vibration_z"],
                        temperature_spindle=tick_data["temperature_spindle"],
                        temperature_coolant=tick_data["temperature_coolant"],
                        current_l1=tick_data["current_l1"],
                        current_l2=tick_data["current_l2"],
                        current_l3=tick_data["current_l3"],
                        pressure_coolant=tick_data["pressure_coolant"],
                        pressure_air=tick_data["pressure_air"],
                        rpm_spindle=tick_data["rpm_spindle"],
                        cutting_force=tick_data["cutting_force"]
                    )
                    db_records.append(t_record)

            # Persist and broadcast
            if db_records:
                async with AsyncSessionLocal() as session:
                    session.add_all(db_records)
                    
                    # Sync machine status changes back to DB
                    for m_id, state in self.physics_states.items():
                        res = await session.execute(select(Machine).filter(Machine.id == m_id))
                        db_m = res.scalars().first()
                        if db_m:
                            db_m.status = state.status
                            db_m.degradation_state = state.degradation_state
                            db_m.active_failure_mode = state.failure_mode
                            db_m.health_score = state.health_score
                            db_m.operating_hours = state.operating_hours

                    await session.commit()

            if telemetry_batch:
                await broadcast_telemetry(telemetry_batch)

        except Exception as e:
            print(f"[Factory Simulator] Error in simulation tick: {e}")

    def start(self):
        if not self.is_running:
            self.scheduler.add_job(self.simulation_tick, 'interval', seconds=settings.SIMULATION_INTERVAL_SECONDS)
            self.scheduler.start()
            self.is_running = True
            print("[Factory Simulator] Scheduler running.")

    def stop(self):
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            print("[Factory Simulator] Scheduler stopped.")

simulator = FactorySimulator()
