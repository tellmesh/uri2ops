from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TaskStep:
    id: str
    uri: str
    operation: str
    kind: str = "query"
    payload: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    expect: dict[str, Any] = field(default_factory=dict)


@dataclass
class OperatorTask:
    id: str
    description: str = ""
    steps: list[TaskStep] = field(default_factory=list)


@dataclass
class StepResult:
    id: str
    uri: str
    operation: str
    kind: str
    status: str
    ok: bool
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        from uri3.results.envelope import enrich_step_dict

        return enrich_step_dict(
            {
                "id": self.id,
                "uri": self.uri,
                "operation": self.operation,
                "kind": self.kind,
                "status": self.status,
                "ok": self.ok,
                "result": self.result,
                "error": self.error,
            }
        )


@dataclass
class TaskResult:
    id: str
    ok: bool
    dry_run: bool
    steps: list[StepResult]

    def to_dict(self) -> dict[str, Any]:
        from uri3.results.envelope import enrich_workflow_dict

        return enrich_workflow_dict(
            {
                "workflow_result": {
                    "id": self.id,
                    "ok": self.ok,
                    "dry_run": self.dry_run,
                },
                "steps": [s.to_dict() for s in self.steps],
            },
            dry_run=self.dry_run,
        )
