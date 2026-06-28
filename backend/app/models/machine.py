from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Machine(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True)
    type = Column(String) # Lathe, Mill, Grinder, CMM
    status = Column(String, default="Offline") # Running, Idle, Fault, Maintenance
    
    # Coordinates for the 3D twin
    pos_x = Column(Float, default=0.0)
    pos_y = Column(Float, default=0.0)
    pos_z = Column(Float, default=0.0)

class Telemetry(Base):
    # This will be converted to a TimescaleDB hypertable
    __tablename__ = "telemetry"
    time = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    machine_id = Column(Integer, ForeignKey("machine.id"), primary_key=True, nullable=False)
    
    # 12 Sensor Channels
    vibration_x = Column(Float)
    vibration_y = Column(Float)
    vibration_z = Column(Float)
    temperature_spindle = Column(Float)
    temperature_coolant = Column(Float)
    current_l1 = Column(Float)
    current_l2 = Column(Float)
    current_l3 = Column(Float)
    pressure_coolant = Column(Float)
    pressure_air = Column(Float)
    rpm_spindle = Column(Float)
    cutting_force = Column(Float)
