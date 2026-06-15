from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen

import yaml

from uri2ops.operation_registry.loader import default_registry_path, load_operation_registry
from uri2ops.operation_registry.models import OperationRegistry, OperationSpec

DEFAULT_CONFIG_PATH = "config/operator_registry.uri.yaml"


def _unwrap_config_document(data: dict[str, Any]) -> dict[str, Any]:
    if (
        data.get("apiVersion") == "uri3.io/v1"
        and data.get("kind")
        and isinstance(data.get("spec"), dict)
    ):
        return dict(data["spec"])
    return data


def registry_config_path(root: Path | None = None) -> Path:
    base = Path(root) if root else Path.cwd()
    return base / DEFAULT_CONFIG_PATH


def load_registry_config(root: Path | None = None) -> dict[str, Any]:
    path = registry_config_path(root)
    if not path.exists():
        return {"version": 1, "local": {"path": str(default_registry_path())}, "remotes": []}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return _unwrap_config_document(data) if isinstance(data, dict) else {}


def _load_source(uri_or_path: str, *, root: Path | None = None) -> dict[str, Any]:
    if uri_or_path.startswith("file://"):
        parsed = urlparse(uri_or_path)
        if parsed.netloc and parsed.netloc not in {"", "localhost"}:
            path = Path(parsed.netloc) / parsed.path.lstrip("/")
        else:
            path = Path(parsed.path)
        if not path.is_absolute() and root is not None:
            path = root / path
    elif "://" in uri_or_path:
        parsed = urlparse(uri_or_path)
        if parsed.scheme in {"http", "https"}:
            with urlopen(uri_or_path, timeout=10) as response:  # noqa: S310
                body = response.read().decode("utf-8")
            if uri_or_path.endswith((".yaml", ".yml")):
                return yaml.safe_load(body) or {}
            return json.loads(body)
        raise ValueError(f"Unsupported remote registry URI: {uri_or_path}")
    else:
        path = Path(uri_or_path)
        if not path.is_absolute() and root is not None:
            path = root / path
    raw = path.read_text(encoding="utf-8")
    if path.suffix in {".yaml", ".yml"}:
        return yaml.safe_load(raw) or {}
    return json.loads(raw)


def merge_registry_documents(*documents: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {"version": 1, "schemes": {}}
    schemes: dict[str, Any] = merged["schemes"]
    for document in documents:
        for scheme, scheme_data in (document.get("schemes") or {}).items():
            bucket = schemes.setdefault(scheme, {"operations": {}})
            bucket.setdefault("operations", {}).update((scheme_data or {}).get("operations") or {})
    return merged


def registry_from_document(
    data: dict[str, Any], *, validate_schema: bool = True
) -> OperationRegistry:
    if validate_schema:
        from uri2ops.operation_registry.validator import validate_registry_schema

        schema_errors = validate_registry_schema(data)
        if schema_errors:
            raise ValueError("Invalid operation registry schema: " + "; ".join(schema_errors[:5]))
    operations: dict[tuple[str, str], OperationSpec] = {}
    for scheme, scheme_data in (data.get("schemes") or {}).items():
        for operation, op_data in (scheme_data.get("operations") or {}).items():
            operations[(scheme, operation)] = OperationSpec.from_mapping(
                scheme, operation, op_data or {}
            )
    return OperationRegistry(operations=operations)


def resolve_operation_registry(
    path: str | Path | None = None,
    *,
    root: Path | None = None,
    include_remote: bool = True,
    validate_schema: bool = True,
) -> OperationRegistry:
    if path is not None:
        return load_operation_registry(path, validate_schema=validate_schema)
    base = Path(root) if root else Path.cwd()
    config = load_registry_config(base)
    local_path = (config.get("local") or {}).get("path") or str(default_registry_path())
    documents = [_load_source(str(local_path), root=base)]
    if include_remote:
        for remote in config.get("remotes") or []:
            if not remote or not remote.get("enabled", True):
                continue
            uri = str(remote.get("uri") or "")
            if not uri:
                continue
            documents.append(_load_source(uri, root=base))
    merged = merge_registry_documents(*documents)
    return registry_from_document(merged, validate_schema=validate_schema)


def registry_document(registry: OperationRegistry) -> dict[str, Any]:
    schemes: dict[str, Any] = {}
    for spec in registry.list():
        schemes.setdefault(spec.scheme, {"operations": {}})
        schemes[spec.scheme]["operations"][spec.operation] = {
            key: value
            for key, value in spec.to_dict().items()
            if key not in {"scheme", "operation"}
        }
    return {"version": 1, "schemes": schemes}


def list_remote_sources(root: Path | None = None) -> list[dict[str, Any]]:
    config = load_registry_config(root)
    local = config.get("local") or {}
    remotes = []
    for remote in config.get("remotes") or []:
        remotes.append(
            {
                "id": remote.get("id"),
                "uri": remote.get("uri"),
                "enabled": bool(remote.get("enabled", True)),
            }
        )
    return [{"kind": "local", "path": local.get("path"), "enabled": True}, *remotes]
