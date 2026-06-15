from __future__ import annotations

from typing import Any

from uri2ops.operation_registry.models import OperationRegistry


def list_mcp_tools(registry: OperationRegistry) -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = []
    for spec in registry.list():
        tools.append(
            {
                "name": f"{spec.scheme}_{spec.operation}",
                "description": f"Run uri2ops operation {spec.scheme}:{spec.operation}",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "uri": {"type": "string"},
                        "payload": {"type": "object"},
                        "adapter": {"type": "string"},
                        "environment": {
                            "type": "string",
                            "enum": ["local", "python", "docker", "mock", "remote"],
                            "description": "Execution environment: local/python (in-process), docker, mock, remote",
                        },
                        "render": {
                            "type": "string",
                            "enum": ["text", "ascii", "markdown", "html", "pdf"],
                        },
                        "approve": {"type": "boolean"},
                        "remote_url": {"type": "string"},
                    },
                    "required": ["uri"],
                },
            }
        )
    tools.append(
        {
            "name": "run_operator_task",
            "description": "Execute a full uri2ops operator task graph.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task": {"type": "object"},
                    "approve": {"type": "boolean"},
                    "dry_run": {"type": "boolean"},
                    "adapter": {"type": "string"},
                },
                "required": ["task"],
            },
        }
    )
    return tools


def mcp_tool_name_for_operation(scheme: str, operation: str) -> str:
    return f"{scheme}_{operation}"
