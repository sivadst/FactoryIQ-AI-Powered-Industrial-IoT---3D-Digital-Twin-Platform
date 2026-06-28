import random
from datetime import datetime, timezone, timedelta
from app.db.session import AsyncSessionLocal
from app.models.oee import WorkOrder
from app.models.machine import Machine

async def generate_work_orders():
    # Randomly generate work orders for machines that are faulted or in maintenance
    now = datetime.now(timezone.utc)
    
    async with AsyncSessionLocal() as session:
        from sqlalchemy.future import select
        result = await session.execute(select(Machine))
        machines = result.scalars().all()
        
        for m in machines:
            if m.status in ["Fault", "Maintenance"]:
                # Check if an open work order exists
                result = await session.execute(
                    select(WorkOrder).filter(WorkOrder.machine_id == m.id, WorkOrder.status == "Open")
                )
                existing = result.scalars().first()
                if not existing:
                    wo = WorkOrder(
                        machine_id=m.id,
                        created_at=now,
                        scheduled_date=now + timedelta(hours=random.randint(1, 48)),
                        type="Corrective" if m.status == "Fault" else "PM",
                        priority=random.choice(["High", "Critical"]) if m.status == "Fault" else "Medium",
                        status="Open",
                        description=f"Auto-generated work order for {m.name} ({m.status})"
                    )
                    session.add(wo)
                    await session.commit()
                    # print(f"Created work order for {m.name}")
