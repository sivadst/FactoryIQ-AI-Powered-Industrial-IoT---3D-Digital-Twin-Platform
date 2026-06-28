from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import AsyncSessionLocal
from app.models.oee import WorkOrder

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/")
async def get_work_orders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WorkOrder))
    return result.scalars().all()
