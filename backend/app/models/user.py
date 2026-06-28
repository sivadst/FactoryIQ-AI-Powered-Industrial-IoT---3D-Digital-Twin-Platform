from sqlalchemy import Column, Integer, String, Boolean
from app.db.base_class import Base

class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="Viewer") # Administrator, Operations Manager, Maintenance Engineer, Production Engineer, Quality Engineer, Viewer
    is_active = Column(Boolean, default=True)
