from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from uri2ops import __version__
from uri2ops.server.environment import list_execution_environments
from uri2ops.server.runtime_profiles import export_environments_payload


class TaskRequest(BaseModel):
    task: dict[str, Any]
    dry_run: bool = False
    approve: bool = False
    adapter: str = "auto"


class McpToolCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


def health_router() -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, Any]:
        return {
            "ok": True,
            "service": "uri2ops",
            "version": __version__,
            "environments": list_execution_environments(),
        }

    @router.get("/environments")
    def environments() -> dict[str, Any]:
        payload = export_environments_payload()
        payload["ok"] = True
        payload["service"] = "uri2ops"
        payload["default"] = (payload.get("defaults") or {}).get("execution_environment", "local")
        return payload

    return router
