from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from datetime import datetime, timezone
from app.db.base_class import Base

class WorkOrder(Base):
    __tablename__ = "work_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    failure_mode = Column(String, default="NONE", nullable=False)
    type = Column(String, default="PREDICTIVE", nullable=False)  # PREDICTIVE, PREVENTIVE, CORRECTIVE, EMERGENCY
    priority = Column(String, default="HIGH", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String, default="OPEN", nullable=False)  # OPEN, ASSIGNED, IN_PROGRESS, COMPLETED, CANCELLED
    
    risk_score = Column(Float, default=0.0)
    predicted_failure = Column(String, nullable=True)
    recommended_action = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    scheduled_date = Column(DateTime(timezone=True), nullable=True)
    assigned_to = Column(String, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    estimated_duration_hours = Column(Float, default=2.0)
    actual_duration_hours = Column(Float, nullable=True)
    parts_required = Column(String, nullable=True)
    completion_notes = Column(Text, nullable=True)
