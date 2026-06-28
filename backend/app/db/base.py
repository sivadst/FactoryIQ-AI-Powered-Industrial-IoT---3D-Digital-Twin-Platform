# Import all the models, so that Base has them before being imported by Alembic
from app.db.base_class import Base
from app.models.user import User
from app.models.machine import Machine, Telemetry
from app.models.oee import OEERecord, WorkOrder
