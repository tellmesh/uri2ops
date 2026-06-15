from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from uri2ops.operator.redaction import redact_event_payload


def events_path(task_id: str, root: str | Path | None = None) -> Path:
    base = Path(root) if root else Path.cwd()
    path = base / "output" / "events" / "operator"
    path.mkdir(parents=True, exist_ok=True)
    return path / f"{task_id}.jsonl"


def append_event(task_id: str, event_type: str, payload: dict[str, Any], root: str | Path | None = None) -> None:
    event = {"type": event_type, "at": int(time.time()), "payload": redact_event_payload(payload)}
    with events_path(task_id, root).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
