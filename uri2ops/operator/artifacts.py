from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from uri2ops.operator.artifact_resolver import resolve_artifact_path


def artifact_root(root: str | Path | None = None) -> Path:
    base = Path(root) if root else Path.cwd()
    path = base / "output" / "artifacts" / "operator"
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_artifact(name: str, payload: dict[str, Any], root: str | Path | None = None) -> str:
    safe = name.replace(":", "_").replace("/", "_")
    file_name = f"{int(time.time() * 1000)}_{safe}.json"
    path = artifact_root(root) / file_name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return f"artifact://operator/{file_name}"


def write_step_artifact(
    task_id: str,
    run_id: str,
    step_id: str,
    suffix: str,
    content: bytes | str,
    *,
    root: str | Path | None = None,
) -> tuple[Path, str]:
    base = Path(root) if root else Path.cwd()
    path = base / "output" / "artifacts" / "operator" / "workflows" / task_id / run_id / step_id / suffix
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_bytes(content)
    uri = f"artifact://operator/workflows/{task_id}/{run_id}/{step_id}/{suffix}"
    return path, uri


def resolve_artifact(uri: str, *, root: str | Path | None = None) -> Path:
    return resolve_artifact_path(uri, root=Path(root) if root else None)


# --- mock helpers (stdlib only) ---

import struct
import zlib


def mock_screenshot_png(width: int = 640, height: int = 360) -> bytes:
    """Valid PNG bytes for mock screenshots (placeholder with banner + banded body).

    Guarantees that .png artifacts written under mock are loadable images, never
    literal text such as "mock-screenshot".
    """
    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(chunk_type + data) & 0xffffffff
        return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    banner_h = max(1, height // 8)
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            if y < banner_h:
                r, g, b = 0x1E, 0x3A, 0x5F
            elif y >= height - max(1, banner_h // 2):
                r, g, b = 0x4A, 0x6A, 0x8A
            else:
                base = 0xE8
                tint = ((x * 2) + (y * 3)) % 24
                r = min(255, base - 10 + tint)
                g = min(255, base - 2 + (tint // 2))
                b = min(255, base + 6)
            raw.extend((r, g, b))
    idat = zlib.compress(bytes(raw), 9)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", idat)
        + _chunk(b"IEND", b"")
    )
