from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timezone

from app.db.session import AsyncSessionLocal
from app.models.machine import Machine
from app.models.telemetry import Telemetry
from app.models.work_order import WorkOrder
from app.models.alert import Alert
from app.simulation.factory_simulator import simulator
from app.core import security

router = APIRouter()

class MachineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    zone: str
    status: str
    criticality: str
    pos_x: float
    pos_y: float
    pos_z: float
    health_score: float
    degradation_state: str
    active_failure_mode: str
    operating_hours: float
    ideal_cycle_time_sec: float

class MachineDetailResponse(MachineResponse):
    active_work_order: Optional[dict] = None
    active_alerts: List[dict] = []

class FailureInjectionRequest(BaseModel):
    failure_mode: str  # BEARING_FAILURE, MOTOR_OVERHEATING, TOOL_WEAR, LUBRICATION_FAILURE, SPINDLE_WEAR, ELECTRICAL_FAULT, COOLANT_FAILURE, VIBRATION_ANOMALY
    severity: Optional[float] = 0.70

class TelemetryPointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    time: datetime
    vibration_x: float
    vibration_y: float
    vibration_z: float
    temperature_spindle: float
    temperature_coolant: float
    current_l1: float
    current_l2: float
    current_l3: float
    pressure_coolant: float
    pressure_air: float
    rpm_spindle: float
    cutting_force: float

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/", response_model=List[MachineResponse])
async def list_machines(
    zone: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    degradation_state: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Machine)
    if zone:
        query = query.filter(Machine.zone == zone)
    if status:
        query = query.filter(Machine.status == status)
    if type:
        query = query.filter(Machine.type == type)
    if degradation_state:
        query = query.filter(Machine.degradation_state == degradation_state)

    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{machine_id}", response_model=MachineDetailResponse)
async def get_machine_detail(
    machine_id: int,
    db: AsyncSession = Depends(get_db)
):
    m_res = await db.execute(select(Machine).filter(Machine.id == machine_id))
    machine = m_res.scalars().first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    # Get active work order
    wo_res = await db.execute(
        select(WorkOrder).filter(
            WorkOrder.machine_id == machine_id,
            WorkOrder.status.in_(["OPEN", "ASSIGNED", "IN_PROGRESS"])
        ).order_by(desc(WorkOrder.created_at))
    )
    active_wo = wo_res.scalars().first()
    active_wo_dict = {
        "id": active_wo.id,
        "title": active_wo.title,
        "priority": active_wo.priority,
        "status": active_wo.status,
        "recommended_action": active_wo.recommended_action
    } if active_wo else None

    # Get active alerts
    alert_res = await db.execute(
        select(Alert).filter(
            Alert.machine_id == machine_id,
            Alert.status == "ACTIVE"
        ).order_by(desc(Alert.timestamp))
    )
    alerts = alert_res.scalars().all()
    active_alerts = [{
        "id": a.id,
        "severity": a.severity,
        "description": a.description,
        "timestamp": a.timestamp
    } for a in alerts]

    data = MachineResponse.model_validate(machine).model_dump()
    data["active_work_order"] = active_wo_dict
    data["active_alerts"] = active_alerts
    return data

@router.get("/{machine_id}/telemetry", response_model=List[TelemetryPointResponse])
async def get_machine_telemetry_history(
    machine_id: int,
    limit: int = Query(60, ge=10, le=500),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Telemetry)
        .filter(Telemetry.machine_id == machine_id)
        .order_by(desc(Telemetry.time))
        .limit(limit)
    )
    result = await db.execute(query)
    points = result.scalars().all()
    return list(reversed(points))

@router.post("/{machine_id}/inject-failure")
async def inject_failure_to_machine(
    machine_id: int,
    req: FailureInjectionRequest,
    db: AsyncSession = Depends(get_db)
):
    valid_modes = [
        "BEARING_FAILURE", "MOTOR_OVERHEATING", "TOOL_WEAR", "LUBRICATION_FAILURE",
        "SPINDLE_WEAR", "ELECTRICAL_FAULT", "COOLANT_FAILURE", "VIBRATION_ANOMALY"
    ]
    if req.failure_mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Invalid failure mode. Allowed: {valid_modes}")

    success = simulator.inject_failure(machine_id, req.failure_mode, req.severity or 0.70)
    if not success:
        raise HTTPException(status_code=404, detail="Machine not active in simulator")

    # Sync DB
    res = await db.execute(select(Machine).filter(Machine.id == machine_id))
    m = res.scalars().first()
    if m:
        m.active_failure_mode = req.failure_mode
        m.degradation_state = "CRITICAL" if req.severity > 0.8 else "ANOMALOUS"
        await db.commit()

    return {"status": "SUCCESS", "message": f"Injected {req.failure_mode} on machine {machine_id}"}

@router.post("/{machine_id}/recover")
async def recover_machine_action(
    machine_id: int,
    db: AsyncSession = Depends(get_db)
):
    simulator.recover_machine(machine_id)
    res = await db.execute(select(Machine).filter(Machine.id == machine_id))
    m = res.scalars().first()
    if m:
        m.status = "Running"
        m.degradation_state = "RECOVERED"
        m.active_failure_mode = "NONE"
        m.health_score = 98.5
        await db.commit()

    return {"status": "SUCCESS", "message": f"Machine {machine_id} recovered to healthy baseline"}
