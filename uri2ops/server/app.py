from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from uri2ops import __version__
from uri2ops.server.routes.a2a import a2a_router
from uri2ops.server.routes.health import health_router
from uri2ops.server.routes.mcp import mcp_router
from uri2ops.server.routes.registry import operations_router, registry_router
from uri2ops.server.routes.tasks import tasks_router
from uri2ops.server.service import OperatorService

# Re-export request models for backward compatibility.
from uri2ops.server.routes.health import McpToolCallRequest, TaskRequest  # noqa: F401


def create_app(
    *,
    root: Path | None = None,
    base_url: str = "http://127.0.0.1:8791",
    registry_path: Path | str | None = None,
    title: str | None = None,
) -> FastAPI:
    service = OperatorService(root=root, registry_path=registry_path)
    app = FastAPI(title=title or "uri2ops", version=__version__)

    for router_factory in (
        lambda: health_router(),
        lambda: registry_router(service),
        lambda: operations_router(service),
        lambda: tasks_router(service),
        lambda: a2a_router(service, base_url),
        lambda: mcp_router(service),
    ):
        app.include_router(router_factory())

    return app
