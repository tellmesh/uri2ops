from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import OperationRegistry, OperationSpec


def default_registry_path() -> Path:
    return Path(__file__).with_name("registry.yaml")


def registry_schema_path() -> Path:
    return Path(__file__).resolve().parents[1] / "schemas" / "operation_registry.schema.json"


def load_operation_registry(path: str | Path | None = None, *, validate_schema: bool = True) -> OperationRegistry:
    registry_path = Path(path) if path else default_registry_path()
    data: dict[str, Any] = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    if validate_schema:
        from .validator import validate_registry_schema

        schema_errors = validate_registry_schema(data)
        if schema_errors:
            raise ValueError("Invalid operation registry schema: " + "; ".join(schema_errors[:5]))
    operations: dict[tuple[str, str], OperationSpec] = {}
    for scheme, scheme_data in (data.get("schemes") or {}).items():
        for operation, op_data in (scheme_data.get("operations") or {}).items():
            spec = OperationSpec.from_mapping(scheme, operation, op_data or {})
            operations[(scheme, operation)] = spec
    return OperationRegistry(operations=operations)
