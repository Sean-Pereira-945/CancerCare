from fastapi.testclient import TestClient

from app.main import app
from app.auth.router import get_current_user
from app.database import get_db
import app.routes.diet as diet_routes


client = TestClient(app)


def _mock_user():
    return {"sub": "02197246-fc3f-4177-84ad-612d1beb780d", "role": "patient"}


class _MockDB:
    def add(self, _obj):
        return None

    def commit(self):
        return None

    def close(self):
        return None


def _mock_get_db():
    db = _MockDB()
    try:
        yield db
    finally:
        db.close()


def test_generate_plan_endpoint(monkeypatch):
    async def _mock_generate_diet_plan(_profile):
        return {
            "plan": {"day_1": {"breakfast": {"meal": "oatmeal"}}},
            "guidelines": {"avoid": ["alcohol"], "emphasize": ["fiber"]},
            "cancer_type": "breast",
        }

    monkeypatch.setattr(diet_routes, "generate_diet_plan", _mock_generate_diet_plan)

    app.dependency_overrides[get_current_user] = _mock_user
    app.dependency_overrides[get_db] = _mock_get_db
    try:
        response = client.post(
            "/api/diet/generate-plan",
            json={
                "cancer_type": "breast",
                "symptoms": ["nausea"],
                "preferences": "high protein",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert "plan" in body
        assert body.get("cancer_type") == "breast"
    finally:
        app.dependency_overrides.clear()


def test_log_meal_endpoint():
    app.dependency_overrides[get_current_user] = _mock_user
    app.dependency_overrides[get_db] = _mock_get_db
    try:
        response = client.post(
            "/api/diet/log-meal",
            json={
                "date": "2026-04-24T12:00:00",
                "meal_type": "lunch",
                "adhered_to_plan": True,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body.get("status") == "Meal logged"
    finally:
        app.dependency_overrides.clear()
