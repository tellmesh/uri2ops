from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_POLICY_PATH = "config/operator_policy.uri.yaml"


@dataclass
class OperatorPolicy:
    require_approval_for: set[str] = field(default_factory=lambda: {"command"})
    allowed_adapters: set[str] = field(
        default_factory=lambda: {"mock", "playwright", "gnome", "builtin", "adb", "uia"}
    )
    operation_overrides: dict[str, dict[str, Any]] = field(default_factory=dict)

    def allows_adapter(self, adapter: str) -> bool:
        return adapter in self.allowed_adapters

    def requires_approval(
        self, *, scheme: str, operation: str, kind: str, registry_requires: bool
    ) -> bool:
        key = f"{scheme}:{operation}"
        override = self.operation_overrides.get(key) or {}
        if "require_approval" in override:
            return bool(override["require_approval"])
        if registry_requires:
            return True
        return kind in self.require_approval_for

    def allowed_adapters_for(
        self, *, scheme: str, operation: str, spec_adapters: list[str]
    ) -> set[str]:
        key = f"{scheme}:{operation}"
        override = self.operation_overrides.get(key) or {}
        if override.get("allowed_adapters"):
            return set(override["allowed_adapters"]) & self.allowed_adapters
        if spec_adapters:
            return set(spec_adapters) & self.allowed_adapters
        return set(self.allowed_adapters)


def default_policy() -> OperatorPolicy:
    return OperatorPolicy()


def _unwrap_config_document(data: dict[str, Any]) -> dict[str, Any]:
    if (
        data.get("apiVersion") == "uri3.io/v1"
        and data.get("kind")
        and isinstance(data.get("spec"), dict)
    ):
        return dict(data["spec"])
    return data


def load_operator_policy(
    path: str | Path | None = None, *, root: Path | None = None
) -> OperatorPolicy:
    base = Path(root) if root else Path.cwd()
    policy_path = Path(path) if path else base / DEFAULT_POLICY_PATH
    if not policy_path.exists():
        return default_policy()
    data = yaml.safe_load(policy_path.read_text(encoding="utf-8")) or {}
    data = _unwrap_config_document(data) if isinstance(data, dict) else {}
    defaults = data.get("defaults") or {}
    overrides = data.get("operations") or {}
    return OperatorPolicy(
        require_approval_for=set(defaults.get("require_approval_for") or ["command"]),
        allowed_adapters=set(
            defaults.get("allowed_adapters")
            or ["mock", "playwright", "gnome", "builtin", "adb", "uia"]
        ),
        operation_overrides={str(key): dict(value or {}) for key, value in overrides.items()},
    )


def policy_config_path(root: Path | None = None) -> Path:
    base = Path(root) if root else Path.cwd()
    return base / DEFAULT_POLICY_PATH
