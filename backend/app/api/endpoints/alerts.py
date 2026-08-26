from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timezone

from app.db.session import AsyncSessionLocal
from app.models.alert import Alert
from app.models.machine import Machine
from app.core import security

router = APIRouter()

class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    machine_id: int
    machine_name: Optional[str] = None
    timestamp: datetime
    severity: str
    type: str
    description: str
    evidence: Optional[str] = None
    status: str
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None

class AcknowledgeRequest(BaseModel):
    acknowledged_by: str = "Operator"

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=5, le=200),
    db: AsyncSession = Depends(get_db)
):
    query = select(Alert).order_by(desc(Alert.timestamp)).limit(limit)
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)

    res = await db.execute(query)
    alerts = res.scalars().all()
    
    # Enrich with machine names
    m_res = await db.execute(select(Machine))
    machines_map = {m.id: m.name for m in m_res.scalars().all()}
    
    out = []
    for a in alerts:
        resp = AlertResponse.model_validate(a)
        resp.machine_name = machines_map.get(a.machine_id, f"MCH-{a.machine_id:03d}")
        out.append(resp)
    return out

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    req: AcknowledgeRequest,
    db: AsyncSession = Depends(get_db),
    user_payload: security.TokenPayload = Depends(security.require_roles(security.UserRole.WRITE_ROLES))
):
    res = await db.execute(select(Alert).filter(Alert.id == alert_id))
    alert = res.scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_by = req.acknowledged_by or user_payload.sub
    await db.commit()
    return {"status": "SUCCESS", "message": f"Alert {alert_id} acknowledged by {alert.acknowledged_by}"}

@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    user_payload: security.TokenPayload = Depends(security.require_roles(security.UserRole.WRITE_ROLES))
):
    res = await db.execute(select(Alert).filter(Alert.id == alert_id))
    alert = res.scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "RESOLVED"
    alert.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "SUCCESS", "message": f"Alert {alert_id} marked as resolved"}

