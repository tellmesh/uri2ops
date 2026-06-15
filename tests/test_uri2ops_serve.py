"""Tests for uri2ops v0.5 serve daemon, remote registry, A2A/MCP wrappers."""

from __future__ import annotations

from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from uri2ops.remote_registry.loader import merge_registry_documents, resolve_operation_registry
from uri2ops.server.adapter import resolve_serve_adapter
from uri2ops.server.app import create_app


def test_resolve_serve_adapter_prefers_arguments_then_payload():
    assert resolve_serve_adapter({}, {"adapter": "playwright"}) == "playwright"
    assert resolve_serve_adapter({"adapter": "mock"}, {"adapter": "playwright"}) == "mock"
    assert resolve_serve_adapter({}, {}) == "auto"


def test_serve_mcp_browser_open_uses_adapter_from_payload(monkeypatch):
    captured: dict[str, str] = {}

    def fake_dispatch(scheme, operation, payload, context, **kwargs):
        captured["adapter"] = context["adapter"]
        return {"ok": True, "url": payload.get("url"), "text": "mock-ok", "adapter": context["adapter"]}

    monkeypatch.setattr("uri2ops.server.routes.mcp.dispatch_with_environment", fake_dispatch)
    client = TestClient(create_app(root=Path.cwd(), base_url="http://testserver"))
    response = client.post(
        "/mcp/tools/call",
        json={
            "name": "browser_open",
            "arguments": {
                "approve": True,
                "payload": {"url": "http://example.com/", "adapter": "playwright"},
            },
        },
    )
    assert response.status_code == 200
    assert captured["adapter"] == "playwright"
    assert response.json()["text"] == "mock-ok"


def test_merge_remote_registry_adds_browser_wait():
    registry = resolve_operation_registry(root=Path.cwd())
    assert registry.get("browser", "wait") is not None


def test_serve_health_and_registry_export():
    client = TestClient(create_app(root=Path.cwd(), base_url="http://testserver"))
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["ok"] is True
    exported = client.get("/registry")
    assert exported.status_code == 200
    assert "browser" in exported.json()["schemes"]
    assert "robot" in exported.json()["schemes"]
    assert "device" in exported.json()["schemes"]


def test_uri2ops_main_exports_asgi_app():
    from uri2ops.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "uri2ops"


def test_serve_agent_card_and_mcp_tools():
    client = TestClient(create_app(root=Path.cwd(), base_url="http://testserver"))
    card = client.get("/.well-known/agent-card.json")
    assert card.status_code == 200
    assert card.json()["name"] == "uri2ops"
    tools = client.get("/mcp/tools")
    assert tools.status_code == 200
    names = {tool["name"] for tool in tools.json()["tools"]}
    assert "browser_open" in names
    assert "robot_state" in names
    assert "device_status" in names
    assert "run_operator_task" in names


def test_serve_run_task_via_a2a():
    task = yaml.safe_load(Path("examples/10_browser_operator/task.health.yaml").read_text(encoding="utf-8"))
    client = TestClient(create_app(root=Path.cwd(), base_url="http://testserver"))
    response = client.post("/a2a/tasks", json={"task": task, "approve": True, "adapter": "mock"})
    assert response.status_code == 200
    body = response.json()
    assert body["workflow_result"]["ok"] is True


def test_serve_mcp_run_operator_task():
    task = yaml.safe_load(Path("examples/10_browser_operator/task.health.yaml").read_text(encoding="utf-8"))
    client = TestClient(create_app(root=Path.cwd(), base_url="http://testserver"))
    response = client.post(
        "/mcp/tools/call",
        json={"name": "run_operator_task", "arguments": {"task": task, "approve": True, "adapter": "mock"}},
    )
    assert response.status_code == 200
    assert response.json()["workflow_result"]["ok"] is True


def test_merge_registry_documents_overlays_operations():
    base = {"version": 1, "schemes": {"browser": {"operations": {"open": {"kind": "command", "handler": "python://x:y", "adapters": ["mock"]}}}}}
    overlay = {"version": 1, "schemes": {"browser": {"operations": {"wait": {"kind": "query", "handler": "python://x:z", "adapters": ["mock"]}}}}}
    merged = merge_registry_documents(base, overlay)
    assert "open" in merged["schemes"]["browser"]["operations"]
    assert "wait" in merged["schemes"]["browser"]["operations"]
