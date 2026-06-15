from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ARTIFACT_SCHEME = "artifact"


def parse_artifact_uri(uri: str) -> tuple[str, ...]:
    parsed = urlparse(uri)
    if parsed.scheme != ARTIFACT_SCHEME:
        raise ValueError(f"Not an artifact URI: {uri!r}")
    path_parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc:
        return (parsed.netloc, *path_parts)
    if not path_parts:
        raise ValueError(f"Artifact URI missing path: {uri!r}")
    return tuple(path_parts)


def resolve_artifact_path(uri: str, *, root: Path | None = None) -> Path:
    parts = parse_artifact_uri(uri)
    base = Path(root) if root else Path.cwd()
    if parts[0] == "operator" and len(parts) >= 2 and parts[1] == "workflows":
        # artifact://operator/workflows/{workflow_id}/{run_id}/{step_id}/{suffix}
        rel = Path("output", "artifacts", *parts)
        return base / rel
    if parts[0] == "operator":
        # artifact://operator/{filename}
        rel = Path("output", "artifacts", "operator", *parts[1:])
        return base / rel
    rel = Path("output", "artifacts", *parts)
    return base / rel


def read_artifact(uri: str, *, root: Path | None = None) -> bytes:
    path = resolve_artifact_path(uri, root=root)
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found for {uri!r}: {path}")
    return path.read_bytes()


def artifact_metadata(uri: str, *, root: Path | None = None) -> dict[str, Any]:
    path = resolve_artifact_path(uri, root=root)
    return {
        "uri": uri,
        "path": str(path),
        "exists": path.exists(),
        "size": path.stat().st_size if path.exists() else 0,
    }
