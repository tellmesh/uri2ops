from __future__ import annotations

import importlib
from typing import Any
from urllib.parse import urlparse

from .loader import load_operation_registry
from uri2ops.remote_registry.loader import resolve_operation_registry
from .models import OperationSpec


def _split_python_uri(uri: str) -> tuple[str, str]:
    parsed = urlparse(uri)
    if parsed.scheme != "python":
        raise ValueError(f"Unsupported handler URI: {uri}")
    target = f"{parsed.netloc}{parsed.path}"
    if ":" not in target:
        raise ValueError(f"Python handler URI must contain module:function: {uri}")
    module_name, func_name = target.split(":", 1)
    return module_name, func_name


def call_handler(spec: OperationSpec, payload: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
    from uri3.config.repo_root import ensure_repo_root_on_syspath

    ensure_repo_root_on_syspath()
    module_name, func_name = _split_python_uri(spec.handler)
    module = importlib.import_module(module_name)
    func = getattr(module, func_name)
    return func(payload, context or {})


def dispatch(scheme: str, operation: str, payload: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = resolve_operation_registry()
    spec = registry.require(scheme, operation)
    return call_handler(spec, payload, context)
