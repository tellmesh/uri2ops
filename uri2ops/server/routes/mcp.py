from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response

from uri2ops.operation_registry.dispatcher import dispatch
from uri2ops.operator.environments.router import dispatch_with_environment
from uri2ops.server.adapter import resolve_serve_adapter
from uri2ops.server.environment import list_execution_environments, resolve_serve_environment
from uri2ops.server.mcp_wrapper import list_mcp_tools, mcp_tool_name_for_operation
from uri2ops.server.renderers.mcp_response import maybe_render_mcp_result, resolve_mcp_render_format
from uri2ops.server.routes.health import McpToolCallRequest, TaskRequest
from uri2ops.server.routes.tasks import run_task_handler
from uri2ops.server.service import OperatorService


def _strip_control_arguments(arguments: dict) -> dict:
    cleaned = dict(arguments)
    cleaned.pop("render", None)
    cleaned.pop("environment", None)
    cleaned.pop("remote_url", None)
    cleaned.pop("operator_url", None)
    return cleaned


def _strip_control_payload(payload: dict) -> dict:
    cleaned = dict(payload)
    cleaned.pop("environment", None)
    cleaned.pop("remote_url", None)
    cleaned.pop("operator_url", None)
    return cleaned


def mcp_router(service: OperatorService) -> APIRouter:
    router = APIRouter()

    @router.get("/mcp/tools")
    def mcp_tools() -> dict:
        return {"tools": list_mcp_tools(service.registry())}

    @router.post("/mcp/tools/call", response_model=None)
    def mcp_tools_call(body: McpToolCallRequest, request: Request):
        render_fmt = resolve_mcp_render_format(
            request.query_params.get("render"),
            body.arguments.get("render"),
        )
        environment = resolve_serve_environment(
            body.arguments,
            body.arguments.get("payload") if isinstance(body.arguments.get("payload"), dict) else None,
        )
        arguments = _strip_control_arguments(body.arguments)

        if body.name == "run_operator_task":
            task = arguments.get("task")
            if not isinstance(task, dict):
                raise HTTPException(status_code=400, detail="arguments.task must be an object")
            result = run_task_handler(
                service,
                TaskRequest(
                    task=task,
                    dry_run=bool(arguments.get("dry_run")),
                    approve=bool(arguments.get("approve")),
                    adapter=resolve_serve_adapter(arguments),
                ),
            )
            return maybe_render_mcp_result(result, render_fmt)

        registry = service.registry()
        for spec in registry.list():
            if mcp_tool_name_for_operation(spec.scheme, spec.operation) != body.name:
                continue
            uri = str(arguments.get("uri") or f"{spec.scheme}://local/{spec.operation}")
            payload = _strip_control_payload(dict(arguments.get("payload") or {}))
            payload.setdefault("target_uri", uri)
            adapter = resolve_serve_adapter(arguments, payload)
            payload.setdefault("adapter", adapter)
            context = {
                "adapter": adapter,
                "task_id": "mcp-call",
                "run_id": body.name,
                "root": str(service.root),
                "session": {},
            }
            if spec.requires_policy and not arguments.get("approve"):
                raise HTTPException(status_code=403, detail=f"{body.name} requires approve=true")
            try:
                result = dispatch_with_environment(
                    spec.scheme,
                    spec.operation,
                    payload,
                    context,
                    environment=environment,
                    control_arguments=arguments,
                )
            except Exception as exc:
                raise HTTPException(status_code=500, detail=str(exc)) from exc
            return maybe_render_mcp_result(result, render_fmt)
        raise HTTPException(status_code=404, detail=f"Unknown MCP tool: {body.name}")

    return router
