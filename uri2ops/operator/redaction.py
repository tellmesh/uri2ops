from __future__ import annotations

import re
from typing import Any

SECRET_KEY_PATTERN = re.compile(r"(password|secret|token|api[_-]?key|credential)", re.I)
REDACTED = "[REDACTED]"


def _is_secret_field(key: str, value: Any) -> bool:
    if SECRET_KEY_PATTERN.search(key):
        return True
    if isinstance(value, dict) and value.get("secret") is True:
        return True
    return False


def redact_value(key: str, value: Any) -> Any:
    if _is_secret_field(key, value):
        return REDACTED
    if isinstance(value, dict):
        if value.get("secret") is True and "value" in value:
            return REDACTED
        return redact_payload(value)
    if isinstance(value, list):
        return [redact_value(key, item) for item in value]
    return value


def redact_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {}
    return {key: redact_value(key, value) for key, value in payload.items()}


def redact_event_payload(payload: dict[str, Any]) -> dict[str, Any]:
    redacted = redact_payload(payload)
    result = redacted.get("result")
    if isinstance(result, dict):
        slim = dict(result)
        for heavy in ("html", "screenshot", "screenshot_uri", "dom", "body"):
            if heavy in slim:
                slim[heavy] = REDACTED if heavy != "screenshot_uri" else slim.get("artifact_uri", REDACTED)
        if "artifact_uri" in result:
            slim.setdefault("artifact_uri", result["artifact_uri"])
        redacted["result"] = slim
    return redacted
