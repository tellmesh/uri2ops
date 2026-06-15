from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from .loader import registry_schema_path
from .models import OperationRegistry

VALID_KINDS = {"query", "command", "assertion"}
VALID_ADAPTER_SETS = {"mock", "playwright", "builtin", "adb", "uia", "gnome"}


def validate_registry_schema(data: dict) -> list[str]:
    schema = json.loads(registry_schema_path().read_text(encoding="utf-8"))
    return [
        f"{list(error.path)}: {error.message}"
        for error in sorted(Draft202012Validator(schema).iter_errors(data), key=lambda item: item.path)
    ]


def validate_operation_registry(registry: OperationRegistry) -> list[str]:
    errors: list[str] = []
    for spec in registry.list():
        if spec.kind not in VALID_KINDS:
            errors.append(f"{spec.scheme}:{spec.operation} invalid kind={spec.kind!r}")
        if not spec.handler.startswith("python://"):
            errors.append(f"{spec.scheme}:{spec.operation} handler must be python://...")
        if ":" not in spec.handler.removeprefix("python://"):
            errors.append(f"{spec.scheme}:{spec.operation} handler must be python://module:function")
        if spec.kind == "command" and not spec.side_effects:
            errors.append(f"{spec.scheme}:{spec.operation} command should declare side_effects=true")
        if spec.side_effects and not spec.requires_policy:
            errors.append(f"{spec.scheme}:{spec.operation} side_effects=true should set requires_policy=true")
        if not spec.adapters:
            errors.append(f"{spec.scheme}:{spec.operation} must declare adapters")
        unknown_adapters = set(spec.adapters) - VALID_ADAPTER_SETS
        if unknown_adapters:
            errors.append(f"{spec.scheme}:{spec.operation} unknown adapters: {sorted(unknown_adapters)!r}")
        if spec.produces_artifact and spec.kind == "command" and spec.scheme not in {"browser", "screen", "android", "pcwin"}:
            errors.append(f"{spec.scheme}:{spec.operation} produces_artifact is unusual for command kind")
    return errors
