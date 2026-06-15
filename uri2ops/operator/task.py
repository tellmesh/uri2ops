from __future__ import annotations

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

    data: dict[str, Any] = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return parse_task(data, default_id=Path(path).stem)
