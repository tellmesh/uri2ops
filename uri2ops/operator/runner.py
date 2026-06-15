from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from uri2ops.operation_registry.dispatcher import call_handler
from uri2ops.operation_registry.loader import load_operation_registry
from uri2ops.remote_registry.loader import resolve_operation_registry
from uri2ops.operation_registry.models import OperationSpec
from uri3.config.repo_root import ensure_repo_root_on_syspath

ensure_repo_root_on_syspath()
from agents.operators.browser_operator.adapters.browser_router import cleanup_browser_session
from uri2ops.operator.policy_loader import load_operator_policy

from .dependency import topological_steps
from .events import append_event
from .models import OperatorTask, StepResult, TaskResult
from .policy import can_execute
from .redaction import redact_payload

BROWSER_SCHEMES = frozenset({"browser", "dom", "screen"})
ANDROID_SCHEMES = frozenset({"android"})
PCWIN_SCHEMES = frozenset({"pcwin"})
SCREEN_SCHEMES = frozenset({"screen"})
INPUT_SCHEMES = frozenset({"input"})


def _scheme(uri: str) -> str:
    return uri.split(":", 1)[0]


def _resolve_value(expr: str, results: dict[str, dict[str, Any]]) -> Any:
    if "." not in expr:
        return results.get(expr)
    step_id, key = expr.split(".", 1)
    value: Any = results.get(step_id, {})
    for part in key.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value


def _hydrate_payload(payload: dict[str, Any], results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    hydrated: dict[str, Any] = {}
    for key, value in payload.items():
        if key == "actual_from" and isinstance(value, str):
            hydrated[key] = _resolve_value(value, results)
        elif isinstance(value, str) and value.endswith(".text"):
            hydrated[key] = _resolve_value(value, results)
        elif isinstance(value, dict) and value.get("secret") is True and "value" in value:
            hydrated[key] = value["value"]
        else:
            hydrated[key] = value
    return hydrated


def _resolve_adapter(spec: OperationSpec, requested: str, runtime_context: dict[str, Any]) -> str:
    if requested == "auto":
        if spec.scheme in BROWSER_SCHEMES:
            from agents.operators.browser_operator.adapters.browser_router import resolve_adapter_mode

            runtime_context["adapter"] = "auto"
            return resolve_adapter_mode(spec.scheme, runtime_context)
        if spec.scheme in ANDROID_SCHEMES:
            from agents.operators.desktop_operator.adapters.android_router import resolve_adapter_mode

            runtime_context["adapter"] = "auto"
            return resolve_adapter_mode(spec.scheme, runtime_context)
        if spec.scheme in PCWIN_SCHEMES:
            from agents.operators.desktop_operator.adapters.pcwin_router import resolve_adapter_mode

            runtime_context["adapter"] = "auto"
            return resolve_adapter_mode(spec.scheme, runtime_context)
        if spec.scheme in SCREEN_SCHEMES:
            from agents.operators.desktop_operator.adapters.screen_router import resolve_adapter_mode

            runtime_context["adapter"] = "auto"
            return resolve_adapter_mode(spec.scheme, runtime_context)
        if spec.scheme in INPUT_SCHEMES:
            from agents.operators.desktop_operator.adapters.input_router import resolve_adapter_mode

            runtime_context["adapter"] = "auto"
            return resolve_adapter_mode(spec.scheme, runtime_context)
        if "builtin" in spec.adapters:
            return "builtin"
        return spec.adapters[0] if spec.adapters else "mock"
    if requested in spec.adapters:
        return requested
    if "builtin" in spec.adapters:
        return "builtin"
    return spec.adapters[0] if spec.adapters else requested


def plan_task(task: OperatorTask, *, root: Path | None = None) -> list[dict[str, Any]]:
    registry = resolve_operation_registry(root=root)
    policy = load_operator_policy(root=root)
    plan: list[dict[str, Any]] = []
    for step in topological_steps(task):
        scheme = _scheme(step.uri)
        spec = registry.require(scheme, step.operation)
        plan.append(
            {
                "id": step.id,
                "uri": step.uri,
                "scheme": scheme,
                "operation": step.operation,
                "kind": spec.kind,
                "side_effects": spec.side_effects,
                "requires_policy": policy.requires_approval(
                    scheme=spec.scheme,
                    operation=spec.operation,
                    kind=spec.kind,
                    registry_requires=spec.requires_policy,
                ),
                "depends_on": step.depends_on,
                "payload": redact_payload(step.payload),
            }
        )
    return plan


def run_task(
    task: OperatorTask,
    *,
    dry_run: bool = False,
    approve: bool = False,
    adapter: str = "mock",
    root: Path | None = None,
) -> TaskResult:
    registry = resolve_operation_registry(root=root)
    policy = load_operator_policy(root=root)
    results: dict[str, dict[str, Any]] = {}
    step_results: list[StepResult] = []
    run_id = uuid4().hex[:12]
    runtime_context: dict[str, Any] = {
        "adapter": adapter,
        "task_id": task.id,
        "run_id": run_id,
        "root": str(root or Path.cwd()),
        "session": {},
    }
    append_event(task.id, "WorkflowStarted", {"dry_run": dry_run, "run_id": run_id}, root=root)

    try:
        for step in topological_steps(task):
            scheme = _scheme(step.uri)
            spec = registry.require(scheme, step.operation)
            step_adapter = _resolve_adapter(spec, adapter, runtime_context)
            runtime_context["adapter"] = step_adapter
            append_event(
                task.id,
                "StepStarted",
                {
                    "step_id": step.id,
                    "uri": step.uri,
                    "operation": step.operation,
                    "adapter": step_adapter,
                    "payload": redact_payload(step.payload),
                },
                root=root,
            )
            allowed, reason = can_execute(spec, approve=approve, adapter=step_adapter, dry_run=dry_run, policy=policy)
            if not allowed:
                result = StepResult(step.id, step.uri, step.operation, spec.kind, "blocked", False, error=reason)
                step_results.append(result)
                append_event(task.id, "StepBlocked", result.to_dict(), root=root)
                continue
            if dry_run:
                result = StepResult(
                    step.id,
                    step.uri,
                    step.operation,
                    spec.kind,
                    "planned",
                    True,
                    result={"handler": spec.handler, "adapter": step_adapter},
                )
                step_results.append(result)
                append_event(task.id, "StepPlanned", result.to_dict(), root=root)
                continue
            payload = _hydrate_payload(step.payload, results)
            payload.setdefault("target_uri", step.uri)
            payload.setdefault("step_id", step.id)
            try:
                output = call_handler(spec, payload, runtime_context)
                ok = bool(output.get("ok", True))
                result = StepResult(
                    step.id,
                    step.uri,
                    step.operation,
                    spec.kind,
                    "completed" if ok else "failed",
                    ok,
                    result=output,
                )
                results[step.id] = output
                step_results.append(result)
                append_event(task.id, "StepCompleted", result.to_dict(), root=root)
            except Exception as exc:
                result = StepResult(step.id, step.uri, step.operation, spec.kind, "failed", False, error=str(exc))
                step_results.append(result)
                append_event(task.id, "StepFailed", result.to_dict(), root=root)
    finally:
        try:
            cleanup_browser_session(runtime_context)
        except Exception:
            pass
    ok = all(step.ok for step in step_results) and not any(step.status == "blocked" for step in step_results)
    append_event(task.id, "WorkflowCompleted", {"ok": ok}, root=root)
    return TaskResult(task.id, ok=ok, dry_run=dry_run, steps=step_results)
