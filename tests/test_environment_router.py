"""Tests for environment router behavior."""

from __future__ import annotations

from uri2ops.operator.environments.router import dispatch_with_environment


def test_dispatch_with_environment_mock_forces_adapter(monkeypatch):
    captured: dict[str, str] = {}

    def fake_dispatch(scheme, operation, payload, context):
        captured["adapter"] = context["adapter"]
        return {"ok": True, "url": payload.get("url"), "text": "ok", "adapter": context["adapter"]}

    monkeypatch.setattr("uri2ops.operator.environments.router.dispatch", fake_dispatch)
    result = dispatch_with_environment(
        "browser",
        "open",
        {"url": "http://example.com/", "adapter": "playwright"},
        {"adapter": "playwright"},
        environment="mock",
    )
    assert captured["adapter"] == "mock"
    assert result["environment"] == "mock"
