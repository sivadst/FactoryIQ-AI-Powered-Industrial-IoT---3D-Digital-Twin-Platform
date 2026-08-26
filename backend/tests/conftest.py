import pytest
import pytest_asyncio
from app.db.init_db import init_db
from app.simulation.factory_simulator import simulator
from app.ml.models import train_and_cache_models

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_suite():
    await init_db()
    train_and_cache_models()
    await simulator.initialize()
    yield
