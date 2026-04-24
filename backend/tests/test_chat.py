import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.router import get_current_user

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()


def test_chat_requires_auth():
    response = client.post("/api/chat/message", json={"message": "hello"})
    # FastAPI/Starlette auth behavior can be 401 or 403 depending on version.
    assert response.status_code in (401, 403)


def test_chat_returns_reply_for_authenticated_user_without_llm_key():
    app.dependency_overrides[get_current_user] = lambda: {"sub": "test-user", "role": "patient"}
    try:
        response = client.post("/api/chat/message", json={"message": "hello"})
        assert response.status_code == 200
        body = response.json()
        assert "reply" in body
        assert "sources_used" in body
    finally:
        app.dependency_overrides.clear()
