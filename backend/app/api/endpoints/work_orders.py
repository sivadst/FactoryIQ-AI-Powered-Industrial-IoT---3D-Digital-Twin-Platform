from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timezone, timedelta

from app.db.session import AsyncSessionLocal
from app.models.work_order import WorkOrder
from app.models.machine import Machine
from app.simulation.work_order_engine import complete_work_order_action
from app.simulation.factory_simulator import simulator
from app.core import security

router = APIRouter()

class WorkOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    machine_id: int
    machine_name: Optional[str] = None
    title: str
    failure_mode: str
    type: str
    priority: str
    status: str
    risk_score: float
    predicted_failure: Optional[str] = None
    recommended_action: Optional[str] = None
    created_at: datetime
    scheduled_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    resolved_at: Optional[datetime] = None
    estimated_duration_hours: float
    parts_required: Optional[str] = None
    completion_notes: Optional[str] = None

class CreateWorkOrderRequest(BaseModel):
    machine_id: int
    title: str
    type: str = "PREVENTIVE"
    priority: str = "HIGH"
    recommended_action: Optional[str] = None
    assigned_to: Optional[str] = None
    estimated_duration_hours: float = 2.0

class AssignTechnicianRequest(BaseModel):
    assigned_to: str

class CompleteWorkOrderRequest(BaseModel):
    technician: str = "Reliability Specialist"
    completion_notes: str
    parts_used: Optional[str] = "Replacement Spindle Bearing Pack"

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/", response_model=List[WorkOrderResponse])
async def list_work_orders(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    limit: int = Query(50, ge=5, le=200),
    db: AsyncSession = Depends(get_db)
):
    query = select(WorkOrder).order_by(desc(WorkOrder.created_at)).limit(limit)
    if status:
        query = query.filter(WorkOrder.status == status)
    if priority:
        query = query.filter(WorkOrder.priority == priority)

    res = await db.execute(query)
    work_orders = res.scalars().all()

    # Fetch machine names
    m_res = await db.execute(select(Machine))
    machines_map = {m.id: m.name for m in m_res.scalars().all()}

    out = []
    for wo in work_orders:
        resp = WorkOrderResponse.model_validate(wo)
        resp.machine_name = machines_map.get(wo.machine_id, f"MCH-{wo.machine_id:03d}")
        out.append(resp)
    return out

@router.post("/", response_model=WorkOrderResponse)
async def create_work_order(
    req: CreateWorkOrderRequest,
    db: AsyncSession = Depends(get_db),
    user_payload: security.TokenPayload = Depends(security.require_roles(security.UserRole.WRITE_ROLES))
):
    now = datetime.now(timezone.utc)
    wo = WorkOrder(
        machine_id=req.machine_id,
        title=req.title,
        failure_mode="MANUAL",
        type=req.type,
        priority=req.priority,
        status="OPEN",
        risk_score=50.0,
        recommended_action=req.recommended_action or "Perform general mechanical inspection",
        created_at=now,
        scheduled_date=now + timedelta(hours=24),
        assigned_to=req.assigned_to,
        estimated_duration_hours=req.estimated_duration_hours
    )
    db.add(wo)
    await db.commit()
    await db.refresh(wo)
    return wo

@router.put("/{work_order_id}/assign")
async def assign_technician(
    work_order_id: int,
    req: AssignTechnicianRequest,
    db: AsyncSession = Depends(get_db),
    user_payload: security.TokenPayload = Depends(security.require_roles(security.UserRole.MAINTENANCE_ROLES))
):
    res = await db.execute(select(WorkOrder).filter(WorkOrder.id == work_order_id))
    wo = res.scalars().first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")

    wo.assigned_to = req.assigned_to
    wo.status = "ASSIGNED"
    await db.commit()
    return {"status": "SUCCESS", "message": f"Work order {work_order_id} assigned to {req.assigned_to}"}

@router.post("/{work_order_id}/complete")
async def complete_work_order(
    work_order_id: int,
    req: CompleteWorkOrderRequest,
    db: AsyncSession = Depends(get_db),
    user_payload: security.TokenPayload = Depends(security.require_roles(security.UserRole.MAINTENANCE_ROLES))
):
    success = await complete_work_order_action(
        work_order_id=work_order_id,
        technician=req.technician,
        completion_notes=req.completion_notes,
        parts_used=req.parts_used or "Standard Kit"
    )
    if not success:
        raise HTTPException(status_code=404, detail="Work order not found or could not be completed")

    res = await db.execute(select(WorkOrder).filter(WorkOrder.id == work_order_id))
    wo = res.scalars().first()
    if wo:
        simulator.recover_machine(wo.machine_id)

    return {
        "status": "SUCCESS",
        "message": f"Work order {work_order_id} completed successfully. Machine recovered and active alerts cleared."
    }

