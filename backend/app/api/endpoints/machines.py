from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import AsyncSessionLocal
from app.models.machine import Machine
from pydantic import BaseModel
from typing import List

router = APIRouter()

class MachineResponse(BaseModel):
    id: int
    name: str
    type: str
    status: str
    pos_x: float
    pos_y: float
    pos_z: float

    class Config:
        from_attributes = True

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/", response_model=List[MachineResponse])
async def read_machines(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Machine))
    return result.scalars().all()
