from __future__ import annotations

from pathlib import Path
from typing import Any

import json
import yaml
from jsonschema import Draft202012Validator

from uri2ops.operation_registry.models import OperationRegistry
from uri2ops.remote_registry.loader import resolve_operation_registry

from .task import load_task, parse_task


def schema_path() -> Path:
    return Path(__file__).resolve().parents[1] / "schemas" / "operator_task.schema.json"


def validate_task_data(data: dict[str, Any], *, registry: OperationRegistry | None = None) -> list[str]:
    schema = json.loads(schema_path().read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(data)]
    if errors:
        return errors
    task = parse_task(data)
    registry = registry or resolve_operation_registry()
    for step in task.steps:
        scheme = step.uri.split(":", 1)[0]
        if not registry.get(scheme, step.operation):
            errors.append(f"Unsupported operation {scheme}:{step.operation} in step {step.id}")
    return errors


def validate_task_file(path: str | Path) -> list[str]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return validate_task_data(data)
