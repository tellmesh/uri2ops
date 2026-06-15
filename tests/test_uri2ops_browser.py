"""Tests for uri2ops browser adapters (mock + optional Playwright)."""

from __future__ import annotations

import http.server
import os
import socket
import sys
import threading
from pathlib import Path

import pytest
from agents.operators.browser_operator.adapters import browser_mock
from agents.operators.browser_operator.adapters.browser_router import resolve_adapter_mode
from uri2ops.operator.runner import run_task
from uri2ops.operator.task import load_task


def test_playwright_import_error_includes_python_executable():
    from agents.operators.browser_operator.adapters.browser_playwright import playwright_import_error

    result = playwright_import_error()
    assert result["error"] == "playwright_not_installed"
    assert sys.executable in result["detail"]
    assert "pip install -e '.[browser]'" in result["detail"]


def test_resolve_adapter_mode_mock():
    assert resolve_adapter_mode("browser", {"adapter": "mock"}) == "mock"


def test_resolve_adapter_mode_auto_falls_back_without_playwright(monkeypatch):
    monkeypatch.setattr(
        "agents.operators.browser_operator.adapters.browser_router._playwright_ready",
        lambda: False,
    )
    assert resolve_adapter_mode("browser", {"adapter": "auto"}) == "mock"


def test_playwright_run_sync_offloads_when_asyncio_loop_active():
    import asyncio

    from agents.operators.browser_operator.adapters import browser_playwright as bp

    seen_on_thread: list[str] = []

    def work() -> str:
        import threading

        seen_on_thread.append(threading.current_thread().name)
        return "ok"

    async def main() -> None:
        assert bp._run_sync(work) == "ok"

    asyncio.run(main())
    assert seen_on_thread
    assert seen_on_thread[0].startswith("uri2ops-playwright")


def test_playwright_cleanup_swallows_greenlet_thread_mismatch():
    from agents.operators.browser_operator.adapters import browser_playwright as bp

    class _BrokenPage:
        def close(self) -> None:
            raise RuntimeError("Cannot switch to a different thread")

    context = {
        "session": {
            "playwright": {
                "page": _BrokenPage(),
                "browser": None,
                "playwright": None,
                "owner_thread": threading.get_ident(),
            }
        }
    }
    bp.close_playwright_session(context)
    assert "playwright" not in context["session"]


def test_mock_task_writes_artifacts(tmp_path: Path):
    task = load_task("examples/10_browser_operator/task.health.yaml")
    result = run_task(task, adapter="mock", approve=True, root=tmp_path)
    assert result.ok is True
    artifacts_dir = tmp_path / "output" / "artifacts" / "operator"
    assert artifacts_dir.exists()
    assert list(artifacts_dir.glob("*.json"))


def test_mock_browser_supplier_report_dom_contains_csv(tmp_path: Path):
    context = {"root": str(tmp_path), "session": {}}
    opened = browser_mock.open_page(
        {"url": "https://supplier-portal.example.local/reports/monthly"},
        context,
    )
    dom = browser_mock.extract_dom({}, context)
    assert opened["ok"] is True
    assert "csv" in dom["text"]


@pytest.mark.skipif(
    os.environ.get("URI2OPS_PLAYWRIGHT_E2E") != "1",
    reason="set URI2OPS_PLAYWRIGHT_E2E=1 for Playwright e2e",
)
def test_playwright_task_executes_against_local_server(tmp_path: Path):
    pytest.importorskip("playwright")
    host = "127.0.0.1"

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body>ok</body></html>")

        def log_message(self, format, *args):  # noqa: A003
            return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, 0))
    port = sock.getsockname()[1]
    sock.close()
    server = http.server.ThreadingHTTPServer((host, port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        from uri2ops.operator.models import OperatorTask, TaskStep

        task = OperatorTask(
            id="browser-health-check",
            description="Playwright health check",
            steps=[
                TaskStep(
                    id="open_health",
                    uri="browser://chrome/page/open",
                    operation="open",
                    kind="command",
                    payload={"url": f"http://{host}:{port}/health"},
                ),
                TaskStep(
                    id="read_dom",
                    uri="browser://chrome/page/active",
                    operation="extract_dom",
                    kind="query",
                    depends_on=["open_health"],
                ),
                TaskStep(
                    id="verify_ok",
                    uri="assertion://contains",
                    operation="check",
                    kind="query",
                    payload={"actual_from": "read_dom.text", "expected": "ok"},
                    depends_on=["read_dom"],
                ),
            ],
        )
        result = run_task(task, adapter="playwright", approve=True, root=tmp_path)
        assert result.ok is True
        assert result.steps[1].result["text"] == "ok"
        workflow_dir = (
            tmp_path
            / "output"
            / "artifacts"
            / "operator"
            / "workflows"
            / "browser-health-check"
        )
        assert (workflow_dir / result.steps[0].id / "open.json").exists() or any(
            workflow_dir.rglob("open.json")
        )
        assert any(workflow_dir.rglob("dom.json"))
    finally:
        server.shutdown()
