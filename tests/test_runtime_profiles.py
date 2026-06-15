"""Tests for runtime environment registry export."""

from __future__ import annotations

from fastapi.testclient import TestClient

from uri2ops.server.app import create_app
from uri2ops.server.runtime_profiles import (
    default_mcp_base_url,
    export_environments_payload,
    operator_profile,
    validate_runtime_registry,
)


def test_export_environments_payload_includes_operators():
    payload = export_environments_payload()
    assert "browser-operator.local" in payload["operators"]
    assert payload["operators"]["browser-operator.local"]["port"] == 8793
    assert "docker" in payload["profiles"]
    assert payload["profiles"]["docker"]["host_requirements"]["host_commands"] == ["docker"]


def test_operator_profile_browser_operator():
    profile = operator_profile("browser-operator.local")
    assert profile is not None
    assert profile["agent_ref"] == "agent://browser-operator"
    assert "8793" in profile["endpoints"]["mcp_call"]


def test_default_mcp_base_url_resolves_browser_and_desktop():
    assert default_mcp_base_url("browser_open") == "http://127.0.0.1:8793"
    assert default_mcp_base_url("browser_extract_dom") == "http://127.0.0.1:8793"
    assert default_mcp_base_url("desktop_click") == "http://127.0.0.1:8791"
    assert default_mcp_base_url("unknown_tool") == "http://127.0.0.1:8791"


def test_environments_endpoint_exports_registry():
    client = TestClient(create_app())
    response = client.get("/environments")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["operators"]["browser-operator.local"]["port"] == 8793
    assert body["profiles"]["local"]["aliases"] == ["python", "host", "inprocess"]


def test_validate_runtime_registry_passes():
    errors = validate_runtime_registry()
    assert errors == []


def test_validate_runtime_registry_schema_rejects_invalid_kind():
    from uri2ops.server.runtime_profiles import validate_runtime_registry_schema

    errors = validate_runtime_registry_schema({"kind": "Wrong"})
    assert errors


def test_validate_runtime_registry_semantics_rejects_unknown_environment():
    from uri2ops.server.runtime_profiles import validate_runtime_registry_semantics

    errors = validate_runtime_registry_semantics(
        {
            "environments": {"bogus": {"label": "bogus"}},
            "operators": {},
        }
    )
    assert any("unknown profile keys" in error for error in errors)


def test_urish_list_environments_local():
    from urish.backends.environments import list_environments

    result = list_environments()
    assert result["ok"] is True
    assert result["data"]["operators"]["browser-operator.local"]["port"] == 8793
