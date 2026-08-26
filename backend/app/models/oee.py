from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from datetime import datetime, timezone
from app.db.base_class import Base

class OEERecord(Base):
    __tablename__ = "oee_records"
    
    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False, index=True)
    time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    # Core OEE metrics
    availability = Column(Float, nullable=False)  # 0.0 to 1.0
    performance = Column(Float, nullable=False)   # 0.0 to 1.0
    quality = Column(Float, nullable=False)       # 0.0 to 1.0
    oee_score = Column(Float, nullable=False)     # 0.0 to 1.0
    
    # Traceable industrial counters
    planned_production_minutes = Column(Float, default=60.0)
    operating_minutes = Column(Float, default=55.0)
    downtime_minutes = Column(Float, default=5.0)
    ideal_cycle_time_sec = Column(Float, default=45.0)
    total_parts_produced = Column(Integer, default=70)
    good_parts_produced = Column(Integer, default=69)
    rejected_parts_produced = Column(Integer, default=1)
    
    # Root downtime reason (if applicable)
    downtime_reason = Column(String, default="NONE")  # NONE, BREAKDOWN, PLANNED_MAINTENANCE, CHANGEOVER, MATERIAL_SHORTAGE, QUALITY_HOLD, OPERATOR_DELAY, OTHER
