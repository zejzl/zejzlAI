"""FastAPI dashboard: public pages, health endpoint and API key middleware.

The TestClient is used without a context manager, so the startup hook
(which connects the bus and providers) does not run.
"""

import pytest
from fastapi.testclient import TestClient

import web_dashboard


@pytest.fixture
def client():
    return TestClient(web_dashboard.app)


def test_root_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_health_detailed_is_public(client):
    response = client.get("/api/health/detailed")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["zejzl"]["bus_status"] == "disconnected"


def test_api_requires_key(client):
    response = client.get("/api/debug/routes")
    assert response.status_code == 401


def test_api_rejects_wrong_key(client, monkeypatch):
    monkeypatch.setenv("ZEJZL_API_KEY_1", "dummy-test-key:free:CI")
    response = client.get("/api/debug/routes", headers={"X-API-Key": "wrong"})
    assert response.status_code == 401


def test_api_accepts_configured_key(client, monkeypatch):
    monkeypatch.setenv("ZEJZL_API_KEY_1", "dummy-test-key:free:CI")
    response = client.get("/api/debug/routes", headers={"X-API-Key": "dummy-test-key"})
    assert response.status_code == 200
    paths = {route["path"] for route in response.json()["routes"]}
    assert "/api/health/detailed" in paths


def test_bearer_header_also_works(client, monkeypatch):
    monkeypatch.setenv("ZEJZL_API_KEY_1", "dummy-test-key:pro:CI")
    response = client.get("/api/debug/routes", headers={"Authorization": "Bearer dummy-test-key"})
    assert response.status_code == 200
