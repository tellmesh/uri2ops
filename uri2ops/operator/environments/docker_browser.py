from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any
from urllib.parse import urlparse, urlunparse

from agents.operators.browser_operator.adapters.browser_router import BROWSER_SCHEMES


def _docker_image() -> str:
    return os.getenv(
        "URI2OPS_DOCKER_PLAYWRIGHT_IMAGE",
        "mcr.microsoft.com/playwright/python:v1.49.1-noble",
    )


def _docker_network(url: str) -> list[str]:
    network = os.getenv("URI2OPS_DOCKER_NETWORK", "host")
    if network:
        return ["--network", network]
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if host in {"localhost", "127.0.0.1", "::1"}:
        return ["--add-host=host.docker.internal:host-gateway"]
    return []


def _rewrite_localhost_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    network = os.getenv("URI2OPS_DOCKER_NETWORK", "host")
    if network == "host" or host not in {"localhost", "127.0.0.1", "::1"}:
        return url
    port = parsed.port
    netloc = "host.docker.internal"
    if port:
        netloc = f"{netloc}:{port}"
    return urlunparse(parsed._replace(netloc=netloc))


def docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        completed = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0


def run_browser_operation_docker(
    operation: str,
    payload: dict[str, Any],
    *,
    timeout_s: float = 120.0,
) -> dict[str, Any]:
    if not docker_available():
        return {
            "ok": False,
            "error": "docker_unavailable",
            "detail": "Docker is not available. Install Docker or use environment=local.",
            "environment": "docker",
        }
    if operation != "open":
        return {
            "ok": False,
            "error": "docker_operation_unsupported",
            "detail": f"docker environment currently supports browser open only, not {operation!r}",
            "environment": "docker",
        }

    url = str(payload.get("url") or payload.get("target_uri") or "about:blank")
    target_url = _rewrite_localhost_url(url)
    timeout_ms = int(payload.get("timeout_ms") or payload.get("navigation_timeout_ms") or 30_000)
    script = """
import json
import sys
from playwright.sync_api import sync_playwright

url = sys.argv[1]
timeout_ms = int(sys.argv[2])
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    page.set_default_navigation_timeout(timeout_ms)
    page.set_default_timeout(timeout_ms)
    response = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    result = {
        "ok": True,
        "url": url,
        "requested_url": sys.argv[3],
        "adapter": "playwright",
        "environment": "docker",
        "title": page.title(),
        "status_code": response.status if response else None,
        "text": page.inner_text("body"),
    }
    browser.close()
print(json.dumps(result, ensure_ascii=False))
"""
    command = [
        "docker",
        "run",
        "--rm",
        *_docker_network(url),
        _docker_image(),
        "python",
        "-c",
        script,
        target_url,
        str(timeout_ms),
        url,
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": "docker_timeout",
            "detail": f"docker browser open timed out after {timeout_s}s",
            "environment": "docker",
            "url": url,
        }
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "docker run failed").strip()
        return {
            "ok": False,
            "error": "docker_run_failed",
            "detail": detail[-4000:],
            "environment": "docker",
            "url": url,
        }
    stdout = completed.stdout.strip()
    if not stdout:
        return {
            "ok": False,
            "error": "docker_empty_output",
            "detail": (completed.stderr or "docker run returned no stdout").strip(),
            "environment": "docker",
            "url": url,
        }
    try:
        result = json.loads(stdout.splitlines()[-1])
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "error": "docker_invalid_output",
            "detail": f"{exc}; stdout={stdout[-1000:]}",
            "environment": "docker",
            "url": url,
        }
    if isinstance(result, dict):
        result.setdefault("environment", "docker")
        result.setdefault("adapter", "playwright")
        result.setdefault("requested_url", url)
    return result


def browser_scheme(scheme: str) -> bool:
    return scheme in BROWSER_SCHEMES or scheme == "browser"
