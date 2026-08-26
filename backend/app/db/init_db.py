import asyncio
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from app.db.session import AsyncSessionLocal, engine
from app.db.base import Base
from app.models.user import User
from app.models.machine import Machine
from app.core.security import get_password_hash, UserRole
from app.core.config import settings

INITIAL_USERS = [
    {"username": "admin", "full_name": "Chief Operations Director", "role": UserRole.ADMIN, "email": "admin@factoryiq.internal"},
    {"username": "plant_mgr", "full_name": "Plant Operations Manager", "role": UserRole.PLANT_MANAGER, "email": "plant_mgr@factoryiq.internal"},
    {"username": "maint_mgr", "full_name": "Maintenance Superintendent", "role": UserRole.MAINTENANCE_MANAGER, "email": "maint_mgr@factoryiq.internal"},
    {"username": "engineer", "full_name": "Lead Reliability Engineer", "role": UserRole.ENGINEER, "email": "engineer@factoryiq.internal"},
    {"username": "operator", "full_name": "Senior Cell Operator", "role": UserRole.OPERATOR, "email": "operator@factoryiq.internal"},
    {"username": "viewer", "full_name": "Audit & Analytics Viewer", "role": UserRole.VIEWER, "email": "viewer@factoryiq.internal"},
]

MACHINE_CONFIGS = [
    # Cell A — CNC Turning (Lathes)
    {"type": "CNC Lathe", "zone": "Cell A — Turning", "criticality": "High", "cycle_time": 35.0},
    {"type": "CNC Lathe", "zone": "Cell A — Turning", "criticality": "High", "cycle_time": 38.0},
    {"type": "CNC Lathe", "zone": "Cell A — Turning", "criticality": "Medium", "cycle_time": 40.0},
    {"type": "CNC Lathe", "zone": "Cell A — Turning", "criticality": "High", "cycle_time": 36.0},
    {"type": "CNC Lathe", "zone": "Cell A — Turning", "criticality": "Critical", "cycle_time": 42.0},
    {"type": "CNC Lathe", "zone": "Cell A — Turning", "criticality": "Medium", "cycle_time": 34.0},

    # Cell B — 5-Axis Milling
    {"type": "5-Axis Mill", "zone": "Cell B — Milling", "criticality": "Critical", "cycle_time": 55.0},
    {"type": "5-Axis Mill", "zone": "Cell B — Milling", "criticality": "Critical", "cycle_time": 60.0},
    {"type": "5-Axis Mill", "zone": "Cell B — Milling", "criticality": "High", "cycle_time": 52.0},
    {"type": "5-Axis Mill", "zone": "Cell B — Milling", "criticality": "Critical", "cycle_time": 58.0},
    {"type": "5-Axis Mill", "zone": "Cell B — Milling", "criticality": "High", "cycle_time": 48.0},
    {"type": "5-Axis Mill", "zone": "Cell B — Milling", "criticality": "Critical", "cycle_time": 65.0},

    # Cell C — Precision Grinding
    {"type": "Surface Grinder", "zone": "Cell C — Grinding", "criticality": "Medium", "cycle_time": 45.0},
    {"type": "Surface Grinder", "zone": "Cell C — Grinding", "criticality": "High", "cycle_time": 50.0},
    {"type": "Surface Grinder", "zone": "Cell C — Grinding", "criticality": "Medium", "cycle_time": 42.0},
    {"type": "Surface Grinder", "zone": "Cell C — Grinding", "criticality": "High", "cycle_time": 47.0},
    {"type": "Surface Grinder", "zone": "Cell C — Grinding", "criticality": "Medium", "cycle_time": 44.0},
    {"type": "Surface Grinder", "zone": "Cell C — Grinding", "criticality": "High", "cycle_time": 49.0},

    # Cell D — QA & CMM Inspection
    {"type": "CMM Inspection", "zone": "Cell D — Quality", "criticality": "Critical", "cycle_time": 30.0},
    {"type": "CMM Inspection", "zone": "Cell D — Quality", "criticality": "Critical", "cycle_time": 30.0},
    {"type": "CMM Inspection", "zone": "Cell D — Quality", "criticality": "High", "cycle_time": 28.0},
    {"type": "CMM Inspection", "zone": "Cell D — Quality", "criticality": "Critical", "cycle_time": 32.0},
    {"type": "CMM Inspection", "zone": "Cell D — Quality", "criticality": "High", "cycle_time": 29.0},
    {"type": "CMM Inspection", "zone": "Cell D — Quality", "criticality": "Critical", "cycle_time": 31.0},
]

async def init_db() -> None:
    async with engine.begin() as conn:
        # Create all tables cleanly
        await conn.run_sync(Base.metadata.create_all)
        
        # If running on PostgreSQL with TimescaleDB extension
        if not settings.USE_SQLITE:
            try:
                await conn.execute(
                    text("SELECT create_hypertable('telemetry', 'time', if_not_exists => TRUE);")
                )
            except Exception as e:
                print(f"[InitDB] TimescaleDB hypertable notice: {e}")

    async with AsyncSessionLocal() as session:
        # 1. Seed RBAC Users
        for u in INITIAL_USERS:
            res = await session.execute(select(User).filter(User.username == u["username"]))
            existing_user = res.scalars().first()
            if not existing_user:
                new_user = User(
                    username=u["username"],
                    email=u["email"],
                    full_name=u["full_name"],
                    hashed_password=get_password_hash("factory123!"),
                    role=u["role"],
                    is_active=True
                )
                session.add(new_user)
        
        # 2. Seed Machines with spatial layout
        res = await session.execute(select(Machine))
        existing_machines = res.scalars().all()
        if not existing_machines:
            print("[InitDB] Initializing realistic 24-machine factory cells...")
            for idx, cfg in enumerate(MACHINE_CONFIGS):
                cell_idx = idx // 6
                pos_in_cell = idx % 6
                row = pos_in_cell // 3
                col = pos_in_cell % 3
                
                # Spatial positioning for 4 distinct industrial bays in the 3D twin
                base_x = (cell_idx % 2) * 50.0 - 25.0
                base_z = (cell_idx // 2) * 50.0 - 25.0
                pos_x = base_x + (col * 14.0 - 14.0)
                pos_z = base_z + (row * 16.0 - 8.0)
                
                machine = Machine(
                    name=f"MCH-{idx+1:03d}",
                    type=cfg["type"],
                    zone=cfg["zone"],
                    status="Running",
                    criticality=cfg["criticality"],
                    pos_x=pos_x,
                    pos_y=0.0,
                    pos_z=pos_z,
                    health_score=round(random.uniform(94.0, 99.5), 1),
                    degradation_state="HEALTHY",
                    active_failure_mode="NONE",
                    operating_hours=round(random.uniform(850.0, 3200.0), 1),
                    ideal_cycle_time_sec=cfg["cycle_time"]
                )
                session.add(machine)
            await session.commit()
            print(f"[InitDB] Seeded {len(MACHINE_CONFIGS)} industrial CNC machines with spatial zones.")
        else:
            await session.commit()

if __name__ == "__main__":
    asyncio.run(init_db())
