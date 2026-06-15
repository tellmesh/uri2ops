from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from uri2ops.server.environment import EXECUTION_ENVIRONMENTS, list_execution_environments

_CANONICAL_ENVIRONMENTS = frozenset({"local", "docker", "mock", "remote"})
_PORT_RE = re.compile(r":(\d+)/")


def registry_schema_path(*, root: Path | None = None) -> Path:
    candidates = [root] if root is not None else []
    candidates.extend([Path.cwd(), *Path.cwd().parents])
    for base in candidates:
        if base is None:
            continue
        path = base / "schemas" / "runtime_environments.schema.json"
        if path.is_file():
            return path
    raise FileNotFoundError("schemas/runtime_environments.schema.json not found")


def _find_registry_path(root: Path | None = None) -> Path | None:
    candidates = [root] if root is not None else []
    candidates.extend([Path.cwd(), *Path.cwd().parents])
    for base in candidates:
        if base is None:
            continue
        path = base / "config" / "runtime_environments.yaml"
        if path.is_file():
            return path
    return None


@lru_cache(maxsize=1)
def load_runtime_registry(*, root: str | None = None) -> dict[str, Any]:
    path = _find_registry_path(Path(root) if root else None)
    if path is None:
        return _builtin_registry()
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _builtin_registry() -> dict[str, Any]:
    return {
        "defaults": {"execution_environment": "local", "policy": "dev", "adapter": "auto"},
        "environments": {
            name: {"label": name}
            for name in sorted(EXECUTION_ENVIRONMENTS)
        },
        "operators": {},
        "control_plane": {},
    }


def export_environments_payload(*, root: str | None = None) -> dict[str, Any]:
    registry = load_runtime_registry(root=root)
    environments = registry.get("environments") or {}
    aliases: dict[str, str] = {}
    for name, spec in environments.items():
        if not isinstance(spec, dict):
            continue
        for alias in spec.get("aliases") or []:
            aliases[str(alias)] = str(name)
    return {
        "defaults": registry.get("defaults") or {},
        "environments": list_execution_environments(),
        "profiles": environments,
        "aliases": aliases,
        "operators": registry.get("operators") or {},
        "control_plane": registry.get("control_plane") or {},
    }


def operator_profile(deployment_id: str, *, root: str | None = None) -> dict[str, Any] | None:
    registry = load_runtime_registry(root=root)
    operators = registry.get("operators") or {}
    profile = operators.get(deployment_id)
    return profile if isinstance(profile, dict) else None


def operator_mcp_base_url(deployment_id: str, *, root: str | None = None) -> str | None:
    profile = operator_profile(deployment_id, root=root)
    if not profile:
        return None
    endpoints = profile.get("endpoints") or {}
    mcp_call = endpoints.get("mcp_call")
    if mcp_call:
        return str(mcp_call).rsplit("/mcp/tools/call", 1)[0]
    port = profile.get("port")
    if port:
        return f"http://127.0.0.1:{port}"
    return None


def default_mcp_base_url(tool: str, *, root: str | None = None) -> str:
    if str(tool).startswith("browser"):
        browser = operator_mcp_base_url("browser-operator.local", root=root)
        if browser:
            return browser
    desktop = operator_mcp_base_url("desktop-operator.local", root=root)
    return desktop or "http://127.0.0.1:8791"


def validate_runtime_registry_schema(data: dict[str, Any], *, root: str | None = None) -> list[str]:
    schema_path = registry_schema_path(root=Path(root) if root else None)
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return [
        f"{list(error.path)}: {error.message}"
        for error in sorted(Draft202012Validator(schema).iter_errors(data), key=lambda item: item.path)
    ]


def validate_runtime_registry_semantics(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    environments = data.get("environments") or {}
    unknown_envs = set(environments) - _CANONICAL_ENVIRONMENTS
    if unknown_envs:
        errors.append(f"environments: unknown profile keys {sorted(unknown_envs)!r}")
    for name, spec in environments.items():
        if not isinstance(spec, dict):
            errors.append(f"environments.{name}: expected mapping")
            continue
        if spec.get("label") and spec["label"] != name:
            errors.append(f"environments.{name}: label must match key ({spec['label']!r})")

    operators = data.get("operators") or {}
    for deployment_id, profile in operators.items():
        if not isinstance(profile, dict):
            errors.append(f"operators.{deployment_id}: expected mapping")
            continue
        port = profile.get("port")
        endpoints = profile.get("endpoints") or {}
        health = str(endpoints.get("health") or "")
        match = _PORT_RE.search(health)
        if port and match and int(match.group(1)) != int(port):
            errors.append(
                f"operators.{deployment_id}: port {port} does not match health endpoint {health!r}"
            )
        default_env = profile.get("default_execution_environment")
        if default_env and default_env not in _CANONICAL_ENVIRONMENTS:
            errors.append(
                f"operators.{deployment_id}: default_execution_environment {default_env!r} is invalid"
            )
    return errors


def validate_runtime_registry(*, root: str | None = None) -> list[str]:
    path = _find_registry_path(Path(root) if root else None)
    if path is None:
        return ["config/runtime_environments.yaml not found"]
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    errors = validate_runtime_registry_schema(data, root=root)
    errors.extend(validate_runtime_registry_semantics(data))
    return errors
