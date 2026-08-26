import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings

@pytest.mark.asyncio
async def test_health_and_ready():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Liveness
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "HEALTHY"
        
        # Readiness
        res = await client.get("/ready")
        assert res.status_code == 200
        assert res.json()["ready"] is True

@pytest.mark.asyncio
async def test_auth_login():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Valid login
        res = await client.post(
            f"{settings.API_V1_STR}/auth/login/access-token",
            data={"username": "admin", "password": "factory123!"}
        )
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["role"] == "ADMIN"

        # Invalid login
        res_fail = await client.post(
            f"{settings.API_V1_STR}/auth/login/access-token",
            data={"username": "admin", "password": "wrongpassword"}
        )
        assert res_fail.status_code == 400

@pytest.mark.asyncio
async def test_machines_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(f"{settings.API_V1_STR}/machines/")
        assert res.status_code == 200
        machines = res.json()
        assert len(machines) > 0
        
        m_id = machines[0]["id"]
        detail_res = await client.get(f"{settings.API_V1_STR}/machines/{m_id}")
        assert detail_res.status_code == 200
        assert detail_res.json()["name"] == machines[0]["name"]

@pytest.mark.asyncio
async def test_ml_evaluation_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(f"{settings.API_V1_STR}/ml/evaluation")
        assert res.status_code == 200
        data = res.json()
        assert "classification" in data
        assert "confusion_matrix" in data["classification"]
        assert "regression_rul" in data

@pytest.mark.asyncio
async def test_oee_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(f"{settings.API_V1_STR}/oee/plant")
        assert res.status_code == 200
        data = res.json()
        assert 0.0 <= data["global_oee"] <= 1.0
        assert 0.0 <= data["availability"] <= 1.0

@pytest.mark.asyncio
async def test_closed_loop_workflow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Fetch Machine 1
        res = await client.get(f"{settings.API_V1_STR}/machines/1")
        assert res.status_code == 200

        # 2. Inject Failure
        inject_res = await client.post(
            f"{settings.API_V1_STR}/machines/1/inject-failure",
            json={"failure_mode": "BEARING_FAILURE", "severity": 0.88}
        )
        assert inject_res.status_code == 200

        # 3. Create Work Order
        wo_res = await client.post(
            f"{settings.API_V1_STR}/work-orders/",
            json={
                "machine_id": 1,
                "title": "Predictive Repair for MCH-001 Spindle Bearing",
                "type": "PREDICTIVE",
                "priority": "CRITICAL",
                "recommended_action": "Replace bearing cartridge"
            }
        )
        assert wo_res.status_code == 200
        wo_id = wo_res.json()["id"]

        # 4. Assign Technician
        assign_res = await client.put(
            f"{settings.API_V1_STR}/work-orders/{wo_id}/assign",
            json={"assigned_to": "Sarah Connor, Lead Reliability Specialist"}
        )
        assert assign_res.status_code == 200

        # 5. Complete Work Order & Verify Recovery
        comp_res = await client.post(
            f"{settings.API_V1_STR}/work-orders/{wo_id}/complete",
            json={
                "technician": "Sarah Connor",
                "completion_notes": "Replaced spindle bearings, aligned axis, balanced at 3500 RPM. Verified vibration back to 0.35 mm/s.",
                "parts_used": "Spindle Bearing Cartridge Kit"
            }
        )
        assert comp_res.status_code == 200
        assert "recovered" in comp_res.json()["message"].lower()
