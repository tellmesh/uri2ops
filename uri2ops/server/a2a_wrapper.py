from __future__ import annotations

from typing import Any

from uri2ops import __version__
from uri2ops.operation_registry.models import OperationRegistry


def build_agent_card(base_url: str, registry: OperationRegistry) -> dict[str, Any]:
    capabilities: list[dict[str, Any]] = []
    for spec in registry.list():
        capabilities.append(
            {
                "name": f"{spec.scheme}_{spec.operation}",
                "description": f"Execute uri2ops operation {spec.scheme}:{spec.operation}",
                "type": "command" if spec.kind == "command" else "query",
                "uri": f"{spec.scheme}:///{spec.operation}",
                "input_schema": spec.input_schema,
                "output_schema": spec.output_schema,
                "requires_policy": spec.requires_policy,
                "adapters": spec.adapters,
            }
        )
    capabilities.append(
        {
            "name": "run_operator_task",
            "description": "Validate, plan, and execute a full uri2ops operator task graph.",
            "type": "command",
            "uri": "a2a://uri2ops/tasks",
            "input_schema": "operator.common.v1.OperatorTask",
            "output_schema": "operator.common.v1.OperatorTaskResult",
        }
    )
    return {
        "name": "uri2ops",
        "version": __version__,
        "description": "URI Operation Registry and Operator Runtime daemon.",
        "capabilities": capabilities,
        "endpoints": {
            "health": f"{base_url.rstrip('/')}/health",
            "tasks": f"{base_url.rstrip('/')}/a2a/tasks",
            "registry": f"{base_url.rstrip('/')}/registry",
            "mcp_tools": f"{base_url.rstrip('/')}/mcp/tools",
        },
    }
