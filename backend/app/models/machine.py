from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base_class import Base

class Machine(Base):
    __tablename__ = "machines"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True, nullable=False)
    type = Column(String, nullable=False)  # CNC Lathe, 5-Axis Mill, Surface Grinder, CMM Inspection
    zone = Column(String, default="Cell A — Turning", nullable=False)  # Cell A, Cell B, Cell C, Cell D
    status = Column(String, default="Running", nullable=False)  # Running, Idle, Fault, Maintenance
    criticality = Column(String, default="High", nullable=False)  # Low, Medium, High, Critical
    
    # 3D Coordinates and spatial orientation
    pos_x = Column(Float, default=0.0)
    pos_y = Column(Float, default=0.0)
    pos_z = Column(Float, default=0.0)
    
    # Machine health & degradation state
    health_score = Column(Float, default=98.5)  # 0.0 to 100.0%
    degradation_state = Column(String, default="HEALTHY")  # HEALTHY, NORMAL_WEAR, EARLY_DEGRADATION, DEGRADING, ANOMALOUS, CRITICAL, FAILED, UNDER_MAINTENANCE, RECOVERED
    active_failure_mode = Column(String, default="NONE")  # NONE, BEARING_FAILURE, MOTOR_OVERHEATING, TOOL_WEAR, LUBRICATION_FAILURE, SPINDLE_WEAR, ELECTRICAL_FAULT, COOLANT_FAILURE, VIBRATION_ANOMALY
    
    operating_hours = Column(Float, default=1240.0)
    ideal_cycle_time_sec = Column(Float, default=45.0)
    last_maintenance_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
