from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Response

from uri2ops.server.renderers.browser_page import (
    is_browser_page_result,
    normalize_render_format,
    render_browser_page,
)


def resolve_mcp_render_format(*values: str | None) -> str | None:
    for value in values:
        if value in (None, ""):
            continue
        try:
            return normalize_render_format(value)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    return None


def maybe_render_mcp_result(result: dict[str, Any], render_fmt: str | None) -> dict[str, Any] | Response:
    if not render_fmt:
        return result
    if not is_browser_page_result(result):
        raise HTTPException(
            status_code=400,
            detail=f"render={render_fmt!r} is supported for browser page results only",
        )
    try:
        body, media_type = render_browser_page(result, render_fmt)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if isinstance(body, bytes):
        return Response(content=body, media_type=media_type)
    return Response(content=body, media_type=f"{media_type}; charset=utf-8")
