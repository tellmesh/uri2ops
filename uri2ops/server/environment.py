from __future__ import annotations

from typing import Any

EXECUTION_ENVIRONMENTS = frozenset({"local", "python", "docker", "mock", "remote"})
DEFAULT_EXECUTION_ENVIRONMENT = "local"

_ENVIRONMENT_ALIASES = {
    "local": "local",
    "host": "local",
    "python": "local",
    "inprocess": "local",
    "docker": "docker",
    "container": "docker",
    "mock": "mock",
    "remote": "remote",
}


def normalize_execution_environment(value: str | None, *, default: str = DEFAULT_EXECUTION_ENVIRONMENT) -> str:
    if value in (None, ""):
        return default
    normalized = _ENVIRONMENT_ALIASES.get(str(value).lower().strip())
    if normalized is None:
        raise ValueError(
            f"unsupported environment: {value!r} "
            f"(expected one of {sorted(EXECUTION_ENVIRONMENTS)})"
        )
    return normalized


def resolve_serve_environment(
    arguments: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    *,
    default: str = DEFAULT_EXECUTION_ENVIRONMENT,
) -> str:
    for source in (arguments or {}, payload or {}):
        value = source.get("environment")
        if value not in (None, ""):
            return normalize_execution_environment(str(value), default=default)
    return default


def list_execution_environments() -> list[str]:
    return sorted(EXECUTION_ENVIRONMENTS)
