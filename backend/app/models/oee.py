from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from app.db.base_class import Base

class OEERecord(Base):
    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machine.id"), index=True)
    time = Column(DateTime(timezone=True), index=True)
    availability = Column(Float)
    performance = Column(Float)
    quality = Column(Float)
    oee_score = Column(Float)

class WorkOrder(Base):
    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machine.id"), index=True)
    created_at = Column(DateTime(timezone=True))
    scheduled_date = Column(DateTime(timezone=True))
    type = Column(String) # PM, Corrective, Predictive
    priority = Column(String) # Low, Medium, High, Critical
    status = Column(String, default="Open")
    description = Column(String)
