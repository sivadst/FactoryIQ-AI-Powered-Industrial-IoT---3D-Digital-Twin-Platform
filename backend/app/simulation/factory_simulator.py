import asyncio
import random
import math
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal, engine
from app.models.machine import Machine, Telemetry
from app.simulation.streamer import broadcast_telemetry
from apscheduler.schedulers.asyncio import AsyncIOScheduler

MACHINES_COUNT = 200

async def init_machines():
    async with AsyncSessionLocal() as session:
        from sqlalchemy.future import select
        result = await session.execute(select(Machine))
        existing_machines = result.scalars().all()
        
        if len(existing_machines) < MACHINES_COUNT:
            print("Initializing factory machines...")
            for i in range(len(existing_machines), MACHINES_COUNT):
                # Simple grid layout for 3D twin
                row = i // 20
                col = i % 20
                
                machine_type = random.choice(["Lathe", "Mill", "Grinder", "CMM"])
                machine = Machine(
                    name=f"MCH-{i:03d}",
                    type=machine_type,
                    status=random.choices(["Running", "Idle", "Fault", "Maintenance"], weights=[0.7, 0.15, 0.05, 0.1])[0],
                    pos_x=float(col * 5),
                    pos_y=0.0,
                    pos_z=float(row * 5)
                )
                session.add(machine)
            await session.commit()
            print(f"Created {MACHINES_COUNT} machines.")
        
        return await session.execute(select(Machine))

async def simulate_telemetry_tick(machine_id: int):
    # Physics inspired generation
    # Vibration grows with bearing wear, temp drifts with coolant
    now = datetime.now(timezone.utc)
    
    t = Telemetry(
        time=now,
        machine_id=machine_id,
        vibration_x=random.gauss(0.5, 0.1),
        vibration_y=random.gauss(0.5, 0.1),
        vibration_z=random.gauss(0.5, 0.1),
        temperature_spindle=random.gauss(65.0, 2.0),
        temperature_coolant=random.gauss(35.0, 1.0),
        current_l1=random.gauss(15.0, 1.5),
        current_l2=random.gauss(15.0, 1.5),
        current_l3=random.gauss(15.0, 1.5),
        pressure_coolant=random.gauss(50.0, 5.0),
        pressure_air=random.gauss(90.0, 2.0),
        rpm_spindle=random.gauss(3000.0, 100.0),
        cutting_force=random.gauss(200.0, 20.0)
    )
    return t

async def generate_and_insert_telemetry():
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy.future import select
            result = await session.execute(select(Machine))
            machines = result.scalars().all()
            
            telemetry_batch = []
            for m in machines:
                if m.status == "Running":
                    t = await simulate_telemetry_tick(m.id)
                    telemetry_batch.append(t)
            
            if telemetry_batch:
                session.add_all(telemetry_batch)
                await session.commit()
                await broadcast_telemetry(telemetry_batch)
    except Exception as e:
        print(f"Error in telemetry generation: {e}")

class FactorySimulator:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(generate_and_insert_telemetry, 'interval', seconds=1)

    def start(self):
        self.scheduler.start()
        print("Factory Simulator started.")
        
    def stop(self):
        self.scheduler.shutdown()
        print("Factory Simulator stopped.")

simulator = FactorySimulator()
