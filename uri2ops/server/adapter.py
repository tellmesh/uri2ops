from __future__ import annotations

from typing import Any


def resolve_serve_adapter(
    arguments: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    *,
    default: str = "auto",
) -> str:
    """Resolve uri2ops adapter from MCP/A2A/REST arguments or step payload."""
    for source in (arguments or {}, payload or {}):
        value = source.get("adapter")
        if value not in (None, ""):
            return str(value)
    return default
