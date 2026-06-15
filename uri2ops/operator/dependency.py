from __future__ import annotations

from .models import OperatorTask, TaskStep


def topological_steps(task: OperatorTask) -> list[TaskStep]:
    by_id = {s.id: s for s in task.steps}
    permanent: set[str] = set()
    temporary: set[str] = set()
    result: list[TaskStep] = []

    def visit(step: TaskStep) -> None:
        if step.id in permanent:
            return
        if step.id in temporary:
            raise ValueError(f"Cycle detected at step {step.id}")
        temporary.add(step.id)
        for dep in step.depends_on:
            if dep not in by_id:
                raise ValueError(f"Missing dependency {dep} referenced by {step.id}")
            visit(by_id[dep])
        temporary.remove(step.id)
        permanent.add(step.id)
        result.append(step)

    for step in task.steps:
        visit(step)
    return result
