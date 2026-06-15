"""Tests for uri2ops v0.1.x features."""

from __future__ import annotations

from pathlib import Path

import yaml

from uri2ops.operation_registry.loader import default_registry_path, load_operation_registry
from uri2ops.operation_registry.validator import validate_operation_registry, validate_registry_schema
from uri2ops.operator.artifact_resolver import read_artifact, resolve_artifact_path
from uri2ops.operator.artifacts import write_artifact
from uri2ops.operator.policy import can_execute
from uri2ops.operator.policy_loader import load_operator_policy
from uri2ops.operator.redaction import redact_payload
from uri2ops.operator.runner import run_task
from uri2ops.operator.task import load_task


def test_redact_secret_payload_field():
    payload = {
        "username": "tom",
        "password": {"value": "s3cr3t", "secret": True},
    }
    redacted = redact_payload(payload)
    assert redacted["username"] == "tom"
    assert redacted["password"] == "[REDACTED]"


def test_registry_schema_validates_yaml():
    data = yaml.safe_load(default_registry_path().read_text(encoding="utf-8"))
    assert validate_registry_schema(data) == []
    assert validate_operation_registry(load_operation_registry()) == []


def test_artifact_resolver_reads_written_file(tmp_path: Path):
    artifact_uri = write_artifact("dom", {"text": "ok"}, root=tmp_path)
    path = resolve_artifact_path(artifact_uri, root=tmp_path)
    assert path.exists()
    assert b"ok" in read_artifact(artifact_uri, root=tmp_path)


def test_policy_allows_gnome_adapter():
    registry = load_operation_registry()
    policy = load_operator_policy(root=Path.cwd())
    screen = registry.require("screen", "observe")
    allowed, reason = can_execute(screen, approve=False, adapter="gnome", dry_run=False, policy=policy)
    assert allowed is True, reason
    typing = registry.require("input", "type")
    allowed, reason = can_execute(typing, approve=True, adapter="gnome", dry_run=False, policy=policy)
    assert allowed is True, reason


def test_policy_blocks_command_without_approve():
    registry = load_operation_registry()
    spec = registry.require("browser", "open")
    policy = load_operator_policy(root=Path.cwd())
    allowed, reason = can_execute(spec, approve=False, adapter="mock", dry_run=False, policy=policy)
    assert allowed is False
    assert reason


def test_registry_includes_pcwin_click():
    registry = load_operation_registry()
    spec = registry.require("pcwin", "click")
    assert spec.handler.endswith(":click")
    assert "mock" in spec.adapters


def test_policy_allows_dry_run_without_approve():
    registry = load_operation_registry()
    spec = registry.require("browser", "open")
    allowed, _ = can_execute(spec, approve=False, adapter="mock", dry_run=True)
    assert allowed is True


def test_task_blocks_without_approve(tmp_path: Path):
    task = load_task("examples/10_browser_operator/task.health.yaml")
    result = run_task(task, adapter="mock", approve=False, root=tmp_path)
    assert result.ok is False
    assert result.steps[0].status == "blocked"
