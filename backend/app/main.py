from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "FactoryIQ API is running."}

from app.api.endpoints import auth, machines, work_orders
from app.api.websockets import stream
from app.simulation.factory_simulator import simulator, init_machines

app.include_router(auth.router, prefix=settings.API_V1_STR + "/auth", tags=["auth"])
app.include_router(machines.router, prefix=settings.API_V1_STR + "/machines", tags=["machines"])
app.include_router(work_orders.router, prefix=settings.API_V1_STR + "/work-orders", tags=["work-orders"])
app.include_router(stream.router, tags=["websockets"])

@app.on_event("startup")
async def startup_event():
    # Ensure database is initialized
    from app.db.init_db import init_db
    await init_db()

    # Ensure models are trained/cached
    from app.ml.models import train_and_cache_models
    train_and_cache_models()
    await init_machines()
    
    # Add OEE calculation to simulator
    from app.simulation.oee_engine import calculate_and_store_oee
    simulator.scheduler.add_job(calculate_and_store_oee, 'interval', seconds=60) # Calculate OEE every minute
    from app.simulation.work_order_engine import generate_work_orders
    simulator.scheduler.add_job(generate_work_orders, 'interval', seconds=120) # Check for WOs every 2 mins
    
    simulator.start()

@app.on_event("shutdown")
def shutdown_event():
    simulator.stop()
