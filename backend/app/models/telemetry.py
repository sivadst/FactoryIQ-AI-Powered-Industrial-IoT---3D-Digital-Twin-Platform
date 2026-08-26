from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Index
from datetime import datetime, timezone
from app.db.base_class import Base

class Telemetry(Base):
    __tablename__ = "telemetry"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False, index=True)
    
    # 12 Industrial Sensor Channels
    vibration_x = Column(Float, nullable=False)
    vibration_y = Column(Float, nullable=False)
    vibration_z = Column(Float, nullable=False)
    temperature_spindle = Column(Float, nullable=False)
    temperature_coolant = Column(Float, nullable=False)
    current_l1 = Column(Float, nullable=False)
    current_l2 = Column(Float, nullable=False)
    current_l3 = Column(Float, nullable=False)
    pressure_coolant = Column(Float, nullable=False)
    pressure_air = Column(Float, nullable=False)
    rpm_spindle = Column(Float, nullable=False)
    cutting_force = Column(Float, nullable=False)

    __table_args__ = (
        Index("idx_telemetry_machine_time", "machine_id", "time"),
    )
