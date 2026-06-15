from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OperationSpec:
    scheme: str
    operation: str
    kind: str
    handler: str
    input_schema: str | None = None
    output_schema: str | None = None
    emits: list[str] = field(default_factory=list)
    side_effects: bool = False
    requires_policy: bool = False
    produces_artifact: bool = False
    adapters: list[str] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, scheme: str, operation: str, data: dict[str, Any]) -> "OperationSpec":
        return cls(
            scheme=scheme,
            operation=operation,
            kind=data.get("kind", "query"),
            handler=data.get("handler", ""),
            input_schema=data.get("input_schema"),
            output_schema=data.get("output_schema"),
            emits=list(data.get("emits", [])),
            side_effects=bool(data.get("side_effects", False)),
            requires_policy=bool(data.get("requires_policy", False)),
            produces_artifact=bool(data.get("produces_artifact", False)),
            adapters=list(data.get("adapters", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scheme": self.scheme,
            "operation": self.operation,
            "kind": self.kind,
            "handler": self.handler,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "emits": self.emits,
            "side_effects": self.side_effects,
            "requires_policy": self.requires_policy,
            "produces_artifact": self.produces_artifact,
            "adapters": self.adapters,
        }


@dataclass
class OperationRegistry:
    operations: dict[tuple[str, str], OperationSpec]

    def get(self, scheme: str, operation: str) -> OperationSpec | None:
        return self.operations.get((scheme, operation))

    def require(self, scheme: str, operation: str) -> OperationSpec:
        spec = self.get(scheme, operation)
        if not spec:
            raise KeyError(f"Unsupported operation: {scheme}:{operation}")
        return spec

    def list(self) -> list[OperationSpec]:
        return list(self.operations.values())
