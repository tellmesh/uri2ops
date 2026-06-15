"""Tests for uri2ops execution environments."""

from __future__ import annotations

from fastapi.testclient import TestClient

from uri2ops.server.adapter import resolve_serve_adapter
from uri2ops.server.app import create_app
from uri2ops.server.environment import normalize_execution_environment, resolve_serve_environment


def test_normalize_execution_environment_aliases():
    assert normalize_execution_environment("python") == "local"
    assert normalize_execution_environment("host") == "local"
    assert normalize_execution_environment("container") == "docker"
    assert normalize_execution_environment(None) == "local"


def test_resolve_serve_environment_prefers_arguments_then_payload():
    assert resolve_serve_environment({"environment": "docker"}, {"environment": "mock"}) == "docker"
    assert resolve_serve_environment({}, {"environment": "python"}) == "local"


def test_health_lists_environments():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert "environments" in body
    assert "docker" in body["environments"]
    assert "python" in body["environments"] or "local" in body["environments"]


def test_serve_mcp_browser_open_environment_mock(monkeypatch):
    captured: dict[str, str] = {}

    def fake_dispatch(scheme, operation, payload, context, *, environment, control_arguments=None, **kwargs):
        captured["environment"] = environment
        captured["adapter"] = context["adapter"]
        return {
            "ok": True,
            "url": payload.get("url"),
            "text": "mock-ok",
            "adapter": "mock",
            "environment": environment,
        }

    monkeypatch.setattr(
        "uri2ops.server.routes.mcp.dispatch_with_environment",
        fake_dispatch,
    )
    client = TestClient(create_app())
    response = client.post(
        "/mcp/tools/call",
        json={
            "name": "browser_open",
            "arguments": {
                "approve": True,
                "environment": "mock",
                "payload": {"url": "http://example.com/", "adapter": "playwright"},
            },
        },
    )
    assert response.status_code == 200
    assert captured["environment"] == "mock"
    assert response.json()["environment"] == "mock"


def test_serve_mcp_browser_open_environment_docker(monkeypatch):
    def fake_dispatch(scheme, operation, payload, context, *, environment, control_arguments=None, **kwargs):
        assert environment == "docker"
        return {
            "ok": True,
            "url": payload["url"],
            "title": "Docker page",
            "text": "docker body",
            "adapter": "playwright",
            "environment": "docker",
        }

    monkeypatch.setattr(
        "uri2ops.server.routes.mcp.dispatch_with_environment",
        fake_dispatch,
    )
    client = TestClient(create_app())
    response = client.post(
        "/mcp/tools/call",
        json={
            "name": "browser_open",
            "arguments": {
                "approve": True,
                "environment": "docker",
                "payload": {"url": "http://localhost:8788/www/", "adapter": "playwright"},
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["environment"] == "docker"
    assert body["title"] == "Docker page"


def test_resolve_serve_adapter_still_works_with_environment():
    assert resolve_serve_adapter({"adapter": "playwright"}, {"adapter": "mock"}) == "playwright"
