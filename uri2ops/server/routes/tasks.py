from __future__ import annotations

from fastapi import APIRouter, HTTPException

from uri2ops.server.routes.health import TaskRequest
from uri2ops.server.service import OperatorService


def run_task_handler(service: OperatorService, body: TaskRequest) -> dict:
    errors = service.validate_task(body.task)
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})
    return service.run_task(
        body.task,
        dry_run=body.dry_run,
        approve=body.approve,
        adapter=body.adapter,
    )


def tasks_router(service: OperatorService) -> APIRouter:
    router = APIRouter()

    @router.post("/validate")
    def validate_task(body: TaskRequest) -> dict:
        errors = service.validate_task(body.task)
        return {"ok": not errors, "errors": errors}

    @router.post("/plan")
    def plan_task(body: TaskRequest) -> dict:
        errors = service.validate_task(body.task)
        if errors:
            raise HTTPException(status_code=400, detail={"errors": errors})
        return {"task": body.task.get("task", {}).get("id"), "plan": service.plan_task(body.task)}

    @router.post("/run")
    def run_task(body: TaskRequest) -> dict:
        return run_task_handler(service, body)

    return router
