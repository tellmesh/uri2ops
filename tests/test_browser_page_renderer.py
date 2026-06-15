"""Tests for browser page MCP renderers."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from uri2ops.server.app import create_app
from uri2ops.server.renderers.browser_page import render_browser_page


SAMPLE = {
    "ok": True,
    "url": "http://localhost:8788/www/",
    "adapter": "playwright",
    "title": "TellMesh — demo",
    "status_code": 200,
    "text": "Hello\nWorld",
    "artifact_uri": "artifact://operator/demo.json",
}


def test_render_browser_page_markdown():
    body, media_type = render_browser_page(SAMPLE, "markdown")
    assert media_type == "text/markdown"
    assert "# TellMesh — demo" in body
    assert "Hello" in body
    assert "playwright" in body


def test_render_browser_page_ascii():
    body, media_type = render_browser_page(SAMPLE, "ascii")
    assert media_type == "text/plain"
    assert "+-" in body
    assert "browser_open" in body
    assert "Hello" in body


def test_render_browser_page_html():
    body, media_type = render_browser_page(SAMPLE, "html")
    assert media_type == "text/html"
    assert "<h1>TellMesh — demo</h1>" in body
    assert "Hello<br>" in body


def test_render_browser_page_text():
    body, media_type = render_browser_page(SAMPLE, "text")
    assert media_type == "text/plain"
    assert "url: http://localhost:8788/www/" in body
    assert "Hello" in body


def test_serve_mcp_browser_open_render_markdown_query(monkeypatch):
    def fake_dispatch(scheme, operation, payload, context, **kwargs):
        return dict(SAMPLE)

    monkeypatch.setattr("uri2ops.server.routes.mcp.dispatch_with_environment", fake_dispatch)
    client = TestClient(create_app())
    response = client.post("/mcp/tools/call?render=markdown", json={"name": "browser_open", "arguments": {"approve": True}})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "# TellMesh — demo" in response.text


def test_serve_mcp_browser_open_render_ascii_argument(monkeypatch):
    def fake_dispatch(scheme, operation, payload, context, **kwargs):
        return dict(SAMPLE)

    monkeypatch.setattr("uri2ops.server.routes.mcp.dispatch_with_environment", fake_dispatch)
    client = TestClient(create_app())
    response = client.post(
        "/mcp/tools/call",
        json={"name": "browser_open", "arguments": {"approve": True, "render": "ascii"}},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "browser_open" in response.text


def test_serve_mcp_browser_open_invalid_render(monkeypatch):
    monkeypatch.setattr(
        "uri2ops.server.routes.mcp.dispatch_with_environment",
        lambda *args, **kwargs: dict(SAMPLE),
    )
    client = TestClient(create_app())
    response = client.post("/mcp/tools/call?render=xml", json={"name": "browser_open", "arguments": {"approve": True}})
    assert response.status_code == 400


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("playwright") is None,
    reason="playwright not installed",
)
def test_render_browser_page_pdf():
    body, media_type = render_browser_page(SAMPLE, "pdf")
    assert media_type == "application/pdf"
    assert body.startswith(b"%PDF")
