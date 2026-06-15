from __future__ import annotations

OPERATION_ALIASES: dict[tuple[str, str], str] = {
    ("browser", "read"): "extract_dom",
    ("browser", "extract"): "extract_dom",
    ("browser", "dom"): "extract_dom",
    ("browser", "body"): "extract_dom",
    ("browser", "active"): "extract_dom",
    ("browser", "capture"): "capture_page",
    ("browser", "screenshot"): "screenshot",
    ("dom", "read"): "extract_dom",
    ("dom", "extract"): "extract_dom",
    ("dom", "extract_dom"): "extract_dom",
    ("dom", "dom"): "extract_dom",
    ("dom", "body"): "extract_dom",
    ("screen", "capture"): "observe",
    ("screen", "screenshot"): "observe",
    ("input", "call"): "type",
    ("input", "type"): "type",
}

SCHEME_ALIASES: dict[str, str] = {
    "dom": "browser",
}


def registry_scheme(scheme: str) -> str:
    return SCHEME_ALIASES.get(scheme, scheme)


def registry_operation(scheme: str, operation: str) -> str:
    return OPERATION_ALIASES.get((scheme, operation), operation)
