from __future__ import annotations

import os
from typing import Any

import httpx

from uri2ops.operation_registry.dispatcher import dispatch
from uri2ops.operator.environments.docker_browser import browser_scheme, run_browser_operation_docker
from uri2ops.server.environment import normalize_execution_environment


def _remote_base_url(arguments: dict[str, Any] | None, payload: dict[str, Any] | None) -> str:
    for source in (arguments or {}, payload or {}):
        value = source.get("remote_url") or source.get("operator_url")
        if value not in (None, ""):
            return str(value).rstrip("/")
    env_value = os.getenv("URI2OPS_REMOTE_URL") or os.getenv("URI2OPS_BASE_URL")
    if env_value:
        return str(env_value).rstrip("/")
    raise ValueError("remote environment requires remote_url, operator_url, or URI2OPS_REMOTE_URL")


def run_browser_operation_remote(
    scheme: str,
    operation: str,
    payload: dict[str, Any],
    arguments: dict[str, Any] | None,
    *,
    timeout_s: float = 120.0,
) -> dict[str, Any]:
    base_url = _remote_base_url(arguments, payload)
    tool_name = f"{scheme}_{operation}"
    body = {
        "name": tool_name,
        "arguments": {
            "approve": True,
            "environment": "local",
            "adapter": payload.get("adapter") or "auto",
            "payload": dict(payload),
        },
    }
    try:
        response = httpx.post(
            f"{base_url}/mcp/tools/call",
            json=body,
            timeout=timeout_s,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return {
            "ok": False,
            "error": "remote_call_failed",
            "detail": str(exc),
            "environment": "remote",
            "remote_url": base_url,
        }
    if "application/json" in response.headers.get("content-type", ""):
        result = response.json()
    else:
        return {
            "ok": False,
            "error": "remote_unexpected_response",
            "detail": response.text[:1000],
            "environment": "remote",
            "remote_url": base_url,
        }
    if isinstance(result, dict):
        result.setdefault("environment", "remote")
        result.setdefault("remote_url", base_url)
    return result


def dispatch_with_environment(
    scheme: str,
    operation: str,
    payload: dict[str, Any],
    context: dict[str, Any],
    *,
    environment: str,
    control_arguments: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = normalize_execution_environment(environment)

    if normalized == "docker" and browser_scheme(scheme):
        return run_browser_operation_docker(operation, payload)

    if normalized == "remote" and browser_scheme(scheme):
        return run_browser_operation_remote(
            scheme,
            operation,
            payload,
            control_arguments,
        )

    dispatch_payload = dict(payload)
    dispatch_context = dict(context)
    if normalized == "mock":
        dispatch_payload["adapter"] = "mock"
        dispatch_context["adapter"] = "mock"

    result = dispatch(scheme, operation, dispatch_payload, dispatch_context)
    if isinstance(result, dict):
        result = dict(result)
        result.setdefault("environment", normalized)
    return result
