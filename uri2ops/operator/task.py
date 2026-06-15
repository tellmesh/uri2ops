from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from uri2ops.operator.models import OperatorTask, TaskStep


def parse_task(data: dict[str, Any], *, default_id: str = "task") -> OperatorTask:
    task_block = data.get("task") or data.get("uri_graph") or {}
    steps: list[TaskStep] = []
    for item in data.get("steps", []) or []:
        steps.append(
            TaskStep(
                id=item["id"],
                uri=item["uri"],
                operation=item.get("operation", "read"),
                kind=item.get("kind", "query"),
                payload=item.get("payload") or {},
                depends_on=list(item.get("depends_on") or []),
                expect=item.get("expect") or {},
            )
        )
    return OperatorTask(
        id=str(task_block.get("id") or default_id),
        description=str(task_block.get("description") or ""),
        steps=steps,
    )


def load_task(path: str | Path) -> OperatorTask:
    import yaml

    task_path = _resolve_task_path(Path(path))
    data: dict[str, Any] = yaml.safe_load(task_path.read_text(encoding="utf-8")) or {}
    return parse_task(data, default_id=task_path.stem)


def _resolve_task_path(path: Path) -> Path:
    if path.is_absolute() or path.exists():
        return path
    if raw := os.getenv("HYPERVISOR_REPO_ROOT"):
        candidate = Path(raw).expanduser() / path
        if candidate.exists():
            return candidate
    for base in (Path.cwd(), Path(__file__).resolve(), *Path(__file__).resolve().parents):
        for root in (base, base / "hypervisor", base / "wronai" / "hypervisor"):
            candidate = root / path
            if candidate.exists():
                return candidate
    return path
