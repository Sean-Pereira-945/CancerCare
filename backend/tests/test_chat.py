import pytest
from fastapi.testclient import TestClient
from app.main import app

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
    assert response.status_code == 403  # no auth token
