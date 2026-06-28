import random
from datetime import datetime, timezone, timedelta
from app.db.session import AsyncSessionLocal
from app.models.oee import OEERecord
from app.models.machine import Machine

async def calculate_and_store_oee():
    now = datetime.now(timezone.utc)
    
    async with AsyncSessionLocal() as session:
        from sqlalchemy.future import select
        result = await session.execute(select(Machine))
        machines = result.scalars().all()
        
        oee_records = []
        for m in machines:
            # Baseline is ~68% with some noise.
            # Running machines have high availability, faulted have 0
            if m.status == "Running":
                avail = random.uniform(0.9, 1.0)
                perf = random.uniform(0.8, 0.95)
                qual = random.uniform(0.9, 0.99)
            elif m.status == "Idle":
                avail = random.uniform(0.5, 0.7)
                perf = 0.0
                qual = 0.0
            else: # Fault / Maintenance
                avail = 0.0
                perf = 0.0
                qual = 0.0
                
            oee_score = avail * perf * qual
            
            record = OEERecord(
                machine_id=m.id,
                time=now,
                availability=avail,
                performance=perf,
                quality=qual,
                oee_score=oee_score
            )
            oee_records.append(record)
            
        if oee_records:
            session.add_all(oee_records)
            await session.commit()
            # print(f"Inserted OEE records for {len(oee_records)} machines")
