from __future__ import annotations

from fastapi import APIRouter, HTTPException

from uri2ops.server.service import OperatorService


def registry_router(service: OperatorService) -> APIRouter:
    router = APIRouter()

    @router.get("/registry")
    def registry_export() -> dict:
        return service.registry_export()

    @router.get("/registry/sources")
    def registry_sources() -> dict:
        return {"sources": service.list_registry_sources()}

    return router


def operations_router(service: OperatorService) -> APIRouter:
    router = APIRouter()

    @router.get("/operations")
    def operations_list() -> dict:
        return {"operations": service.list_operations()}

    @router.get("/operations/{scheme}/{operation}")
    def operations_describe(scheme: str, operation: str) -> dict:
        try:
            return service.describe_operation(scheme, operation).to_dict()
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return router
