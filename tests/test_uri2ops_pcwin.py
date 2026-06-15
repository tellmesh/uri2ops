"""Tests for uri2ops Windows pcwin adapter (mock + optional UIA)."""

from __future__ import annotations

import os
import sys

import pytest

from agents.operators.desktop_operator.adapters.pcwin_router import resolve_adapter_mode
from agents.operators.desktop_operator.adapters.pcwin_uri import parse_pcwin_uri
from agents.operators.desktop_operator.adapters.pcwin_uia import uia_available
from uri2ops.operator.runner import run_task
from uri2ops.operator.task import load_task


def test_parse_pcwin_window_uri():
    target_type, target_id, action = parse_pcwin_uri("pcwin://window/Notepad/focus")
    assert target_type == "window"
    assert target_id == "Notepad"
    assert action == "focus"


def test_parse_pcwin_control_uri():
    target_type, target_id, action = parse_pcwin_uri("pcwin://control/SaveButton/click")
    assert target_type == "control"
    assert target_id == "SaveButton"
    assert action == "click"


def test_parse_pcwin_path_only_form():
    target_type, target_id, action = parse_pcwin_uri("pcwin:///window/Notepad/focus")
    assert target_type == "window"
    assert target_id == "Notepad"
    assert action == "focus"


def test_resolve_adapter_mode_mock():
    assert resolve_adapter_mode("pcwin", {"adapter": "mock"}) == "mock"


def test_resolve_adapter_mode_auto_on_linux():
    assert resolve_adapter_mode("pcwin", {"adapter": "auto"}) == "mock"


def test_pcwin_mock_task(tmp_path):
    task = load_task("examples/13_pcwin_operator/task.pcwin.yaml")
    result = run_task(task, adapter="mock", approve=True, root=tmp_path)
    assert result.ok is True
    assert result.steps[0].result["focused"] is True
    assert result.steps[1].result["clicked"] is True
    workflow_dir = tmp_path / "output" / "artifacts" / "operator" / "workflows" / "notepad-save-smoke"
    assert any(workflow_dir.rglob("focus.json"))
    assert any(workflow_dir.rglob("click.json"))


def test_pcwin_blocked_without_approve(tmp_path):
    task = load_task("examples/13_pcwin_operator/task.pcwin.yaml")
    result = run_task(task, adapter="mock", approve=False, root=tmp_path)
    assert result.ok is False
    assert result.steps[0].status == "blocked"


@pytest.mark.skipif(os.environ.get("URI2OPS_PCWIN_E2E") != "1", reason="set URI2OPS_PCWIN_E2E=1 for Windows UIA e2e")
def test_pcwin_uia_available_only_on_windows():
    if sys.platform != "win32":
        pytest.skip("Windows only")
    assert uia_available() or pytest.importorskip("pywinauto")
