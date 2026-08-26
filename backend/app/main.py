import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("FactoryIQ")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing FactoryIQ Enterprise Backend...")
    
    # 1. Initialize Database Schema & Seed Data
    from app.db.init_db import init_db
    await init_db()
    
    # 2. Verify & Cache AI/ML Model Weights
    from app.ml.models import train_and_cache_models
    train_and_cache_models()
    
    # 3. Initialize Factory Simulator & Physics Engine
    from app.simulation.factory_simulator import simulator
    await simulator.initialize()
    
    # 4. Schedule Industrial OEE & Closed-Loop Work Order Jobs
    from app.simulation.oee_engine import calculate_and_store_oee
    from app.simulation.work_order_engine import evaluate_and_generate_work_orders
    
    simulator.scheduler.add_job(
        calculate_and_store_oee,
        'interval',
        seconds=settings.OEE_CALCULATION_INTERVAL_SECONDS
    )
    simulator.scheduler.add_job(
        evaluate_and_generate_work_orders,
        'interval',
        seconds=settings.WORK_ORDER_INTERVAL_SECONDS
    )
    
    # 5. Start Real-time Telemetry Loop
    simulator.start()
    logger.info("FactoryIQ Industrial Simulator and Streaming Engine Online.")
    
    yield
    
    logger.info("Shutting down FactoryIQ Simulator...")
    simulator.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS if not settings.DEBUG else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "OPERATIONAL",
        "docs": f"{settings.API_V1_STR}/docs"
    }

# Import Routers
from app.api.endpoints import auth, machines, alerts, work_orders, oee, ml_analytics, health
from app.api.websockets import stream

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication & RBAC"])
app.include_router(machines.router, prefix=f"{settings.API_V1_STR}/machines", tags=["Machines & Failure Injection"])
app.include_router(alerts.router, prefix=f"{settings.API_V1_STR}/alerts", tags=["Alert & Incident Center"])
app.include_router(work_orders.router, prefix=f"{settings.API_V1_STR}/work-orders", tags=["Closed-Loop Work Orders"])
app.include_router(oee.router, prefix=f"{settings.API_V1_STR}/oee", tags=["OEE & Downtime Analytics"])
app.include_router(ml_analytics.router, prefix=f"{settings.API_V1_STR}/ml", tags=["AI/ML Model Center"])
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["Observability & Health"])
app.include_router(health.router, tags=["Root Health"])
app.include_router(stream.router, tags=["Real-time Streaming WebSockets"])
