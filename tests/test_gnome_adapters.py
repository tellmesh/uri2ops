from __future__ import annotations

from agents.operators.desktop_operator.adapters.input_router import (
    resolve_adapter_mode,
    type_text,
)
from agents.operators.desktop_operator.adapters.screen_router import (
    observe,
    resolve_adapter_mode as screen_mode,
)


def test_screen_router_mock_observe():
    result = observe({"step_id": "observe", "target_uri": "screen://desktop/observe"}, {"adapter": "mock"})
    assert result["ok"] is True
    assert result["artifact_uri"].startswith("artifact://")


def test_input_router_mock_type():
    result = type_text({"step_id": "type", "text": "echo autonomy"}, {"adapter": "mock"})
    assert result["ok"] is True


def test_screen_router_gnome_mode_when_unavailable(monkeypatch):
    monkeypatch.setattr(
        "agents.operators.desktop_operator.adapters.screen_router._gnome_ready",
        lambda: False,
    )
    assert screen_mode("screen", {"adapter": "auto"}) == "mock"


def test_input_router_gnome_mode_when_unavailable(monkeypatch):
    monkeypatch.setattr(
        "agents.operators.desktop_operator.adapters.input_router._gnome_ready",
        lambda: False,
    )
    assert resolve_adapter_mode("input", {"adapter": "auto"}) == "mock"
