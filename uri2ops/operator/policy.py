from __future__ import annotations

from uri2ops.operation_registry.models import OperationSpec
from uri2ops.operator.policy_loader import OperatorPolicy, load_operator_policy


def can_execute(
    spec: OperationSpec,
    *,
    approve: bool,
    adapter: str = "mock",
    dry_run: bool = False,
    policy: OperatorPolicy | None = None,
) -> tuple[bool, str | None]:
    policy = policy or load_operator_policy()
    if not policy.allows_adapter(adapter):
        return False, f"Adapter {adapter!r} is not allowed by operator policy"
    allowed = policy.allowed_adapters_for(
        scheme=spec.scheme,
        operation=spec.operation,
        spec_adapters=spec.adapters,
    )
    if adapter not in allowed:
        return False, f"Adapter {adapter!r} not allowed for {spec.scheme}:{spec.operation}"
    if dry_run:
        return True, None
    if policy.requires_approval(
        scheme=spec.scheme,
        operation=spec.operation,
        kind=spec.kind,
        registry_requires=spec.requires_policy,
    ) and not approve:
        return False, f"Operation {spec.scheme}:{spec.operation} requires --approve"
    return True, None
