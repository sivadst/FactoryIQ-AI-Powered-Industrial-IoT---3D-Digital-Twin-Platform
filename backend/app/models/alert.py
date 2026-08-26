from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Index
from datetime import datetime, timezone
from app.db.base_class import Base

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    severity = Column(String, default="WARNING", nullable=False)  # INFO, WARNING, CRITICAL
    type = Column(String, nullable=False)  # ANOMALY, PREDICTED_FAILURE, SENSOR_SPIKE, OEE_DROP, DOWNTIME
    description = Column(String, nullable=False)
    evidence = Column(Text, nullable=True)  # JSON or descriptive feature triggers
    status = Column(String, default="ACTIVE", nullable=False)  # ACTIVE, ACKNOWLEDGED, RESOLVED
    acknowledged_by = Column(String, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_alerts_status_machine", "status", "machine_id"),
    )
