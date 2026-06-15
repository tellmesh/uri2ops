"""Tests for uri2ops Android adapter (mock + optional ADB)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from agents.operators.desktop_operator.adapters.android_adb import adb_available, list_devices
from agents.operators.desktop_operator.adapters.android_router import resolve_adapter_mode
from agents.operators.desktop_operator.adapters.android_uri import parse_android_uri
from uri2ops.operator.runner import run_task
from uri2ops.operator.task import load_task


def test_parse_android_uri():
    device_id, action = parse_android_uri("android://device/emulator-5554/screenshot")
    assert device_id == "emulator-5554"
    assert action == "screenshot"


def test_resolve_adapter_mode_mock():
    assert resolve_adapter_mode("android", {"adapter": "mock"}) == "mock"


def test_resolve_adapter_mode_auto_without_adb(monkeypatch):
    monkeypatch.setattr("agents.operators.desktop_operator.adapters.android_router._adb_ready", lambda: False)
    assert resolve_adapter_mode("android", {"adapter": "auto"}) == "mock"


def test_android_mock_task(tmp_path: Path):
    task = load_task("examples/12_android_operator/task.android.yaml")
    result = run_task(task, adapter="mock", approve=True, root=tmp_path)
    assert result.ok is True
    assert result.steps[0].result["artifact_uri"].startswith("artifact://operator/workflows/")
    assert "Settings" in result.steps[1].result["xml"]
    workflow_dir = tmp_path / "output" / "artifacts" / "operator" / "workflows" / "android-settings-smoke"
    assert any(workflow_dir.rglob("screenshot.png"))
    assert any(workflow_dir.rglob("ui_dump.xml"))


def test_android_tap_blocked_without_approve(tmp_path: Path):
    task = load_task("examples/12_android_operator/task.android.yaml")
    result = run_task(task, adapter="mock", approve=False, root=tmp_path)
    assert result.ok is False
    assert any(step.status == "blocked" for step in result.steps)


@pytest.mark.skipif(os.environ.get("URI2OPS_ANDROID_E2E") != "1", reason="set URI2OPS_ANDROID_E2E=1 for adb e2e")
def test_android_adb_task_when_device_present(tmp_path: Path):
    if not adb_available() or not list_devices():
        pytest.skip("adb device not connected")
    device_id = list_devices()[0]
    from uri2ops.operator.models import OperatorTask, TaskStep

    task = OperatorTask(
        id="android-adb-smoke",
        description="ADB screenshot",
        steps=[
            TaskStep(
                id="screenshot_home",
                uri=f"android://device/{device_id}/screenshot",
                operation="screenshot",
                kind="query",
            )
        ],
    )
    result = run_task(task, adapter="adb", approve=True, root=tmp_path)
    assert result.ok is True
    assert result.steps[0].result["bytes"] > 0
