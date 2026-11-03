"""FastAPI dashboard: public pages, health endpoint and API key middleware.

The TestClient is used without a context manager, so the startup hook
(which connects the bus and providers) does not run.
"""

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import web_dashboard


ORDINARY_KEY = "dummy-test-key"
ADMIN_KEY = "dummy-admin-key"


@pytest.fixture
def client():
    return TestClient(web_dashboard.app)


@pytest.fixture
def keys(monkeypatch):
    """One ordinary (pro) key and one admin key."""
    monkeypatch.setenv("ZEJZL_API_KEY_1", f"{ORDINARY_KEY}:pro:CI user")
    monkeypatch.setenv("ZEJZL_API_KEY_2", f"{ADMIN_KEY}:admin:CI admin")


@pytest.fixture
def security_manager(monkeypatch, tmp_path):
    """A fresh MCP security manager wired into the dashboard (default principals only)."""
    from src.mcp_security import MCPSecurityManager

    manager = MCPSecurityManager(audit_log_path=str(tmp_path / "audit.log"))
    monkeypatch.setattr(web_dashboard.dashboard, "mcp_security_manager", manager)
    return manager


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


# --- F04: WebSockets need the same API key as /api/* -------------------------


@pytest.mark.parametrize("path", ["/ws/blackboard", "/ws/live"])
def test_websocket_without_key_is_rejected(client, keys, path):
    with pytest.raises(WebSocketDisconnect) as info:
        with client.websocket_connect(path):
            pass
    assert info.value.code == 1008


@pytest.mark.parametrize("path", ["/ws/blackboard", "/ws/live"])
def test_websocket_with_wrong_key_is_rejected(client, keys, path):
    with pytest.raises(WebSocketDisconnect) as info:
        with client.websocket_connect(f"{path}?api_key=wrong"):
            pass
    assert info.value.code == 1008


def test_blackboard_websocket_accepts_query_param_key(client, keys):
    with client.websocket_connect(f"/ws/blackboard?api_key={ORDINARY_KEY}") as ws:
        frame = ws.receive_json()
    assert "timestamp" in frame
    assert "blackboard" in frame


def test_live_websocket_accepts_header_key(client, keys):
    with client.websocket_connect("/ws/live", headers={"X-API-Key": ORDINARY_KEY}) as ws:
        frame = ws.receive_json()
    assert isinstance(frame, dict)
    assert frame


# --- F21: enum values are lowercase; F03: creation needs an admin key ---------


def test_create_principal_lowercase_level_and_permissions(client, keys, security_manager):
    response = client.post(
        "/api/mcp/security/principals",
        json={
            "id": "alice",
            "name": "Alice",
            "security_level": "user",
            "permissions": ["read_tools", "CALL_TOOLS"],
        },
        headers={"X-API-Key": ADMIN_KEY},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["principal"]["security_level"] == "user"
    assert sorted(body["principal"]["permissions"]) == ["call_tools", "read_tools"]
    assert "alice" in security_manager.principals


def test_create_principal_unknown_level_is_400(client, keys, security_manager):
    response = client.post(
        "/api/mcp/security/principals",
        json={"id": "bob", "name": "Bob", "security_level": "root"},
        headers={"X-API-Key": ADMIN_KEY},
    )
    assert response.status_code == 400
    assert "bob" not in security_manager.principals


def test_create_principal_with_ordinary_key_is_403(client, keys, security_manager):
    response = client.post(
        "/api/mcp/security/principals",
        json={"id": "eve", "name": "Eve", "security_level": "admin"},
        headers={"X-API-Key": ORDINARY_KEY},
    )
    assert response.status_code == 403
    assert "eve" not in security_manager.principals


# --- F03: tokens and approvals are bound to the authenticated key -------------


def test_token_for_other_principal_with_ordinary_key_is_403(client, keys, security_manager):
    response = client.post(
        "/api/mcp/security/tokens",
        json={"principal_id": "system"},
        headers={"X-API-Key": ORDINARY_KEY},
    )
    assert response.status_code == 403
    assert security_manager.tokens == {}


def test_token_with_admin_key_succeeds(client, keys, security_manager):
    response = client.post(
        "/api/mcp/security/tokens",
        json={"principal_id": "system", "permissions": ["read_tools"]},
        headers={"X-API-Key": ADMIN_KEY},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["token"]
    assert len(security_manager.tokens) == 1
    token = next(iter(security_manager.tokens.values()))
    assert token.principal_id == "system"
    assert [p.value for p in token.permissions] == ["read_tools"]


def test_token_unknown_permission_is_400(client, keys, security_manager):
    response = client.post(
        "/api/mcp/security/tokens",
        json={"principal_id": "system", "permissions": ["launch_rockets"]},
        headers={"X-API-Key": ADMIN_KEY},
    )
    assert response.status_code == 400
    assert security_manager.tokens == {}


@pytest.fixture
def pending_approval(monkeypatch):
    """Seed one admin-level pending approval and return its id."""
    from src.security_validator import (
        ApprovalRequirement,
        RiskLevel,
        ValidationResult,
        security_validator,
    )

    validation = ValidationResult(
        is_safe=False,
        risk_level=RiskLevel.HIGH_RISK,
        approval_required=ApprovalRequirement.ADMIN_APPROVE,
        violations=[],
        recommendations=[],
        requires_user_approval=False,
        requires_admin_approval=True,
        can_proceed=False,
    )
    approval_id = "approval_test_1"
    monkeypatch.setitem(
        security_validator.pending_approvals,
        approval_id,
        {
            "operation": "rm -rf /tmp/x",
            "validation": validation,
            "user_id": "requester",
            "timestamp": 0.0,
            "status": "pending",
        },
    )
    return approval_id


def test_approve_with_ordinary_key_is_403(client, keys, pending_approval):
    from src.security_validator import security_validator

    response = client.post(
        "/api/security/approve",
        json={"approval_id": pending_approval, "approved": True, "admin_user": "mallory"},
        headers={"X-API-Key": ORDINARY_KEY},
    )
    assert response.status_code == 403
    assert security_validator.pending_approvals[pending_approval]["status"] == "pending"


def test_approve_takes_approver_from_auth_not_body(client, keys, pending_approval):
    from src.security_validator import security_validator

    response = client.post(
        "/api/security/approve",
        json={"approval_id": pending_approval, "approved": True, "admin_user": "mallory"},
        headers={"X-API-Key": ADMIN_KEY},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    approval = security_validator.pending_approvals[pending_approval]
    assert approval["status"] == "approved"
    assert approval["approved_by"] == "ZEJZL_API_KEY_2"
    assert "mallory" not in str(approval["approved_by"])
