from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from datetime import datetime, timezone
from app.db.base_class import Base

class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False, index=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=True, index=True)
    
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    action_taken = Column(String, nullable=False)
    technician = Column(String, nullable=False)
    parts_replaced = Column(String, nullable=True)
    downtime_minutes = Column(Float, default=0.0)
    pre_health_score = Column(Float, default=0.0)
    post_health_score = Column(Float, default=100.0)
    verification_status = Column(String, default="VERIFIED_HEALTHY")  # VERIFIED_HEALTHY, MONITORING, RE_INSPECT
    notes = Column(Text, nullable=True)
