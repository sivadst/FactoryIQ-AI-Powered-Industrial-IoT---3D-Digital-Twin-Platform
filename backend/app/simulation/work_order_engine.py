import random
from datetime import datetime, timezone, timedelta
from sqlalchemy.future import select
from app.db.session import AsyncSessionLocal
from app.models.work_order import WorkOrder
from app.models.machine import Machine
from app.models.alert import Alert
from app.models.maintenance_log import MaintenanceLog
from app.ml.xai_rca import RCA_KNOWLEDGE_BASE

async def evaluate_and_generate_work_orders():
    """
    Closed-loop predictive maintenance trigger:
    Inspects machine health and degradation states. If risk/anomaly is critical,
    creates structured Predictive Work Orders and raises centralized alerts.
    """
    now = datetime.now(timezone.utc)
    
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Machine))
            machines = result.scalars().all()
            
            for m in machines:
                needs_work_order = False
                wo_type = "PREDICTIVE"
                wo_priority = "HIGH"
                failure_mode = m.active_failure_mode if m.active_failure_mode != "NONE" else "BEARING_FAILURE"
                
                if m.status in ("Fault", "Maintenance"):
                    needs_work_order = True
                    wo_type = "CORRECTIVE" if m.status == "Fault" else "PREVENTIVE"
                    wo_priority = "CRITICAL" if m.status == "Fault" else "MEDIUM"
                elif m.degradation_state in ("ANOMALOUS", "CRITICAL", "FAILED"):
                    needs_work_order = True
                    wo_type = "PREDICTIVE"
                    wo_priority = "CRITICAL" if m.degradation_state in ("CRITICAL", "FAILED") else "HIGH"

                if needs_work_order:
                    # Check if an open/active work order already exists for this machine
                    existing_wo = await session.execute(
                        select(WorkOrder).filter(
                            WorkOrder.machine_id == m.id,
                            WorkOrder.status.in_(["OPEN", "ASSIGNED", "IN_PROGRESS"])
                        )
                    )
                    if not existing_wo.scalars().first():
                        kb = RCA_KNOWLEDGE_BASE.get(failure_mode, RCA_KNOWLEDGE_BASE["BEARING_FAILURE"])
                        
                        wo = WorkOrder(
                            machine_id=m.id,
                            title=f"Predictive Intervention: {m.name} ({failure_mode.replace('_', ' ')})",
                            failure_mode=failure_mode,
                            type=wo_type,
                            priority=wo_priority,
                            status="OPEN",
                            risk_score=85.0 if wo_priority == "CRITICAL" else 65.0,
                            predicted_failure=failure_mode,
                            recommended_action=kb["recommended_action"],
                            created_at=now,
                            scheduled_date=now + timedelta(hours=random.randint(2, 12)),
                            estimated_duration_hours=2.5,
                            parts_required=f"{kb['subsystem']} Replacement Kit"
                        )
                        session.add(wo)

                        # Create corresponding alarm in Alert Center
                        existing_alert = await session.execute(
                            select(Alert).filter(
                                Alert.machine_id == m.id,
                                Alert.status == "ACTIVE"
                            )
                        )
                        if not existing_alert.scalars().first():
                            alert = Alert(
                                machine_id=m.id,
                                timestamp=now,
                                severity="CRITICAL" if wo_priority == "CRITICAL" else "WARNING",
                                type="PREDICTED_FAILURE",
                                description=f"AI detected impending {failure_mode.replace('_', ' ')} on {m.name}. Risk elevated.",
                                evidence=kb["evidence_template"],
                                status="ACTIVE"
                            )
                            session.add(alert)

            await session.commit()
    except Exception as e:
        print(f"[Work Order Engine] Error generating work orders: {e}")

async def complete_work_order_action(
    work_order_id: int,
    technician: str,
    completion_notes: str,
    parts_used: str = "Standard Kit"
) -> bool:
    """
    Execute maintenance recovery on a machine:
    1. Mark work order as COMPLETED.
    2. Reset machine state back to Running / HEALTHY / RECOVERED.
    3. Log historical MaintenanceLog audit record.
    4. Auto-resolve associated active alerts.
    """
    now = datetime.now(timezone.utc)
    try:
        async with AsyncSessionLocal() as session:
            wo_res = await session.execute(select(WorkOrder).filter(WorkOrder.id == work_order_id))
            wo = wo_res.scalars().first()
            if not wo:
                return False

            wo.status = "COMPLETED"
            wo.resolved_at = now
            wo.assigned_to = technician
            wo.completion_notes = completion_notes
            wo.actual_duration_hours = wo.estimated_duration_hours

            # Retrieve Machine
            m_res = await session.execute(select(Machine).filter(Machine.id == wo.machine_id))
            machine = m_res.scalars().first()
            if machine:
                pre_health = machine.health_score
                machine.status = "Running"
                machine.degradation_state = "RECOVERED"
                machine.active_failure_mode = "NONE"
                machine.health_score = 98.5
                machine.last_maintenance_at = now

                # Log maintenance record
                log = MaintenanceLog(
                    machine_id=machine.id,
                    work_order_id=wo.id,
                    timestamp=now,
                    action_taken=f"Resolved {wo.failure_mode}: {completion_notes}",
                    technician=technician,
                    parts_replaced=parts_used,
                    downtime_minutes=float(wo.estimated_duration_hours * 60.0),
                    pre_health_score=pre_health,
                    post_health_score=98.5,
                    verification_status="VERIFIED_HEALTHY",
                    notes=completion_notes
                )
                session.add(log)

            # Auto-resolve active alerts for this machine
            alert_res = await session.execute(
                select(Alert).filter(Alert.machine_id == wo.machine_id, Alert.status == "ACTIVE")
            )
            for alert in alert_res.scalars().all():
                alert.status = "RESOLVED"
                alert.acknowledged_by = technician
                alert.resolved_at = now

            await session.commit()
            return True
    except Exception as e:
        print(f"[Work Order Engine] Error completing work order: {e}")
        return False
