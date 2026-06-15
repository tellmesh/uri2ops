from __future__ import annotations

from fastapi import APIRouter

from uri2ops.server.a2a_wrapper import build_agent_card
from uri2ops.server.routes.health import TaskRequest
from uri2ops.server.routes.tasks import run_task_handler
from uri2ops.server.service import OperatorService


def a2a_router(service: OperatorService, base_url: str) -> APIRouter:
    router = APIRouter()

    @router.get("/.well-known/agent-card.json")
    def agent_card() -> dict:
        return build_agent_card(base_url, service.registry())

    @router.post("/a2a/tasks")
    def a2a_tasks(body: TaskRequest) -> dict:
        return run_task_handler(service, body)

    return router
