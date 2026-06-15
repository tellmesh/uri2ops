from __future__ import annotations

from pathlib import Path

from uri2ops.operator.runner import plan_task, run_task
from uri2ops.operator.task import load_task
from uri2ops.operator.validator import validate_task_file
from uri2ops.remote_registry.loader import resolve_operation_registry


def test_physical_ops_registry_contains_robot_and_device(repo_root: Path):
    registry = resolve_operation_registry(root=repo_root)

    assert registry.get("robot", "state") is not None
    assert registry.get("robot", "move") is not None
    assert registry.get("robot", "stop") is not None
    assert registry.get("robot", "mission_start") is not None
    assert registry.get("device", "status") is not None
    assert registry.get("device", "read") is not None
    assert registry.get("device", "write") is not None


def test_physical_robot_task_runs_with_mock_adapter(repo_root: Path):
    path = repo_root / "examples/36_physical_ops/task.robot.yaml"

    assert validate_task_file(path) == []
    task = load_task(path)
    plan = plan_task(task, root=repo_root)
    assert [step["scheme"] for step in plan[:3]] == ["robot", "robot", "robot"]

    result = run_task(task, adapter="mock", approve=True, root=repo_root)
    payload = result.to_dict()
    assert payload["workflow_result"]["ok"] is True
    assert payload["steps"][0]["result"]["robot_id"] == "amr-1"
    assert payload["steps"][1]["result"]["command"] == "move"
    assert payload["steps"][2]["result"]["command"] == "stop"


def test_physical_device_task_runs_with_mock_adapter(repo_root: Path):
    path = repo_root / "examples/36_physical_ops/task.device.yaml"

    assert validate_task_file(path) == []
    task = load_task(path)
    result = run_task(task, adapter="mock", approve=True, root=repo_root)
    payload = result.to_dict()
    assert payload["workflow_result"]["ok"] is True
    assert payload["steps"][0]["result"]["device_id"] == "sensor-1"
    assert payload["steps"][1]["result"]["channel"] == "temperature"
    assert payload["steps"][2]["result"]["device_id"] == "relay-1"
