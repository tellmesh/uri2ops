from __future__ import annotations

import html
import textwrap
from typing import Any

RENDER_FORMATS = frozenset({"json", "text", "ascii", "markdown", "html", "pdf"})


def normalize_render_format(value: str | None) -> str | None:
    if value in (None, ""):
        return None
    fmt = str(value).lower().strip()
    if fmt == "md":
        fmt = "markdown"
    if fmt not in RENDER_FORMATS:
        raise ValueError(f"unsupported render format: {value!r} (expected one of {sorted(RENDER_FORMATS)})")
    return None if fmt == "json" else fmt


def is_browser_page_result(result: dict[str, Any]) -> bool:
    if not isinstance(result, dict):
        return False
    if not result.get("url"):
        return False
    return any(key in result for key in ("title", "text", "status_code", "adapter"))


def render_browser_page(result: dict[str, Any], fmt: str) -> tuple[str | bytes, str]:
    normalized = normalize_render_format(fmt)
    if normalized is None:
        raise ValueError(f"render format must not be json: {fmt!r}")
    fields = _extract_fields(result)
    if normalized == "text":
        return _render_text(fields), "text/plain"
    if normalized == "ascii":
        return _render_ascii(fields), "text/plain"
    if normalized == "markdown":
        return _render_markdown(fields), "text/markdown"
    if normalized == "html":
        return _render_html(fields), "text/html"
    if normalized == "pdf":
        return _render_pdf(fields), "application/pdf"
    raise ValueError(f"unsupported render format: {fmt!r}")


def _extract_fields(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(result.get("ok")),
        "url": str(result.get("url") or ""),
        "title": str(result.get("title") or ""),
        "adapter": str(result.get("adapter") or ""),
        "environment": str(result.get("environment") or ""),
        "status_code": result.get("status_code"),
        "text": str(result.get("text") or ""),
        "artifact_uri": str(result.get("artifact_uri") or ""),
        "error": str(result.get("error") or ""),
        "detail": str(result.get("detail") or ""),
    }


def _status_line(fields: dict[str, Any]) -> str:
    if fields["error"]:
        return f"FAIL {fields['error']}"
    status = fields["status_code"]
    status_part = f" status={status}" if status is not None else ""
    adapter = fields["adapter"] or "unknown"
    env = fields["environment"] or "local"
    return f"OK browser_open adapter={adapter} environment={env}{status_part}"


def _render_text(fields: dict[str, Any]) -> str:
    lines = [_status_line(fields)]
    if fields["url"]:
        lines.append(f"url: {fields['url']}")
    if fields["title"]:
        lines.append(f"title: {fields['title']}")
    if fields["artifact_uri"]:
        lines.append(f"artifact: {fields['artifact_uri']}")
    if fields["detail"]:
        lines.append(f"detail: {fields['detail']}")
    if fields["text"]:
        lines.extend(["", "---", fields["text"]])
    return "\n".join(lines).strip() + "\n"


def _render_ascii(fields: dict[str, Any]) -> str:
    width = 78
    inner = width - 4

    def row(label: str, value: str) -> list[str]:
        wrapped = textwrap.wrap(value, width=inner - len(label) - 1) or [""]
        out = [f"| {label:<8} {wrapped[0]:<{inner - 9}} |"]
        for continuation in wrapped[1:]:
            out.append(f"| {'':8} {continuation:<{inner - 9}} |")
        return out

    top = "+" + "-" * (width - 2) + "+"
    header = f"| {'browser_open':<{width - 4}} |"
    sep = "+" + "-" * (width - 2) + "+"
    body: list[str] = [top, header, sep]
    body.extend(row("status", _status_line(fields)))
    if fields["url"]:
        body.extend(row("url", fields["url"]))
    if fields["title"]:
        body.extend(row("title", fields["title"]))
    if fields["artifact_uri"]:
        body.extend(row("artifact", fields["artifact_uri"]))
    if fields["detail"]:
        body.extend(row("detail", fields["detail"]))
    body.append(sep)
    if fields["text"]:
        body.append(f"| {'content':<{width - 4}} |")
        body.append(sep)
        for line in fields["text"].splitlines()[:40]:
            for wrapped in textwrap.wrap(line, width=inner) or [""]:
                body.append(f"| {wrapped:<{width - 4}} |")
        if fields["text"].count("\n") >= 40:
            body.append(f"| {'... truncated ...':<{width - 4}} |")
    body.append(top)
    return "\n".join(body) + "\n"


def _render_markdown(fields: dict[str, Any]) -> str:
    title = fields["title"] or "Browser page"
    lines = [f"# {title}", ""]
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Status | `{_status_line(fields)}` |")
    if fields["url"]:
        lines.append(f"| URL | `{fields['url']}` |")
    if fields["adapter"]:
        lines.append(f"| Adapter | `{fields['adapter']}` |")
    if fields["environment"]:
        lines.append(f"| Environment | `{fields['environment']}` |")
    if fields["status_code"] is not None:
        lines.append(f"| HTTP status | `{fields['status_code']}` |")
    if fields["artifact_uri"]:
        lines.append(f"| Artifact | `{fields['artifact_uri']}` |")
    if fields["detail"]:
        lines.append(f"| Detail | {fields['detail']} |")
    if fields["text"]:
        lines.extend(["", "## Page text", "", "```text", fields["text"], "```"])
    return "\n".join(lines).strip() + "\n"


def _render_html(fields: dict[str, Any]) -> str:
    title = html.escape(fields["title"] or "Browser page")
    meta_rows = [
        ("Status", html.escape(_status_line(fields))),
        ("URL", html.escape(fields["url"])),
        ("Adapter", html.escape(fields["adapter"])),
        ("Environment", html.escape(fields["environment"])),
        ("HTTP status", html.escape(str(fields["status_code"] if fields["status_code"] is not None else ""))),
        ("Artifact", html.escape(fields["artifact_uri"])),
        ("Detail", html.escape(fields["detail"])),
    ]
    rows = "".join(
        f"<tr><th>{label}</th><td>{value or '—'}</td></tr>"
        for label, value in meta_rows
        if value
    )
    body_text = html.escape(fields["text"]).replace("\n", "<br>\n")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    body {{ font-family: Inter, ui-sans-serif, system-ui, sans-serif; margin: 24px; color: #0f172a; background: #e9eef3; }}
    main {{ max-width: 960px; margin: 0 auto; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 12px; padding: 24px; }}
    h1 {{ margin-top: 0; }}
    table {{ width: 100%; border-collapse: collapse; margin: 16px 0 24px; }}
    th, td {{ text-align: left; vertical-align: top; padding: 8px 10px; border-bottom: 1px solid #dbe3ea; }}
    th {{ width: 140px; color: #475569; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #eef2f6; padding: 16px; border-radius: 8px; }}
  </style>
</head>
<body>
  <main>
    <h1>{title}</h1>
    <table>{rows}</table>
    <h2>Page text</h2>
    <pre>{body_text}</pre>
  </main>
</body>
</html>
"""


def _render_pdf(fields: dict[str, Any]) -> bytes:
    page_html = _render_html(fields)
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PDF render requires Playwright. Install with: pip install -e '.[browser]' "
            "&& python -m playwright install chromium"
        ) from exc
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.set_content(page_html, wait_until="domcontentloaded")
            return page.pdf(format="A4", print_background=True)
        finally:
            browser.close()
