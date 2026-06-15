from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from uri2ops.operation_registry.loader import load_operation_registry
from uri2ops.operation_registry.validator import validate_operation_registry
from uri2ops.operator.runner import plan_task, run_task
from uri2ops.operator.task import load_task
from uri2ops.operator.validator import validate_task_file
from uri2ops.remote_registry.loader import list_remote_sources, resolve_operation_registry


def _print(data) -> None:
    print(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


def operations_cmd(args) -> int:
    registry = resolve_operation_registry()
    if args.action == "list":
        _print({"operations": [spec.to_dict() for spec in registry.list()]})
        return 0
    if args.action == "describe":
        spec = registry.require(args.scheme, args.operation)
        _print(spec.to_dict())
        return 0
    if args.action == "validate":
        errors = validate_operation_registry(registry)
        if errors:
            _print({"ok": False, "errors": errors})
            return 1
        _print({"ok": True})
        return 0
    raise SystemExit(f"Unknown operations action: {args.action}")


def registry_cmd(args) -> int:
    if args.action == "list":
        _print({"sources": list_remote_sources()})
        return 0
    if args.action == "validate":
        registry = resolve_operation_registry()
        errors = validate_operation_registry(registry)
        if errors:
            _print({"ok": False, "errors": errors})
            return 1
        _print({"ok": True, "operations": len(registry.list())})
        return 0
    raise SystemExit(f"Unknown registry action: {args.action}")


def validate_cmd(args) -> int:
    errors = validate_task_file(args.path)
    if errors:
        _print({"ok": False, "errors": errors})
        return 1
    _print({"ok": True, "path": args.path})
    return 0


def plan_cmd(args) -> int:
    task = load_task(args.path)
    _print({"task": task.id, "plan": plan_task(task)})
    return 0


def run_cmd(args) -> int:
    task = load_task(args.path)
    result = run_task(task, dry_run=args.dry_run, approve=args.approve, adapter=args.adapter)
    _print(result.to_dict())
    return 0 if result.ok else 2


def serve_cmd(args) -> int:
    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit(
            'uvicorn is required for uri2ops serve: pip install -e "packages/uri2ops[server]"'
        ) from exc
    from uri2ops.server.app import create_app

    base_url = f"http://{args.host}:{args.port}"
    app = create_app(root=Path.cwd(), base_url=base_url)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


def environments_cmd(args) -> int:
    from uri2ops.server.runtime_profiles import export_environments_payload

    if args.action == "validate":
        from uri2ops.server.runtime_profiles import validate_runtime_registry

        errors = validate_runtime_registry(root=args.root)
        payload = {"ok": not errors, "errors": errors}
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            _print(payload)
        return 0 if not errors else 1

    payload = export_environments_payload(root=args.root)
    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _print(payload)
    return 0


def mcp_call_cmd(args) -> int:
    import httpx

    from uri2ops.server.runtime_profiles import default_mcp_base_url

    arguments = json.loads(args.arguments)
    if args.environment:
        arguments["environment"] = args.environment
    if args.render:
        arguments["render"] = args.render
    payload = {"name": args.tool, "arguments": arguments}
    params = {"render": args.render} if args.render else None
    base_url = args.base_url or default_mcp_base_url(args.tool)
    url = f"{base_url.rstrip('/')}/mcp/tools/call"
    response = httpx.post(url, json=payload, params=params, timeout=args.timeout)
    if response.status_code >= 400:
        print(response.text, file=sys.stderr)
        return 1
    content_type = response.headers.get("content-type", "")
    if "application/pdf" in content_type:
        out = sys.stdout.buffer
        if args.output:
            Path(args.output).write_bytes(response.content)
        else:
            out.write(response.content)
        return 0
    text = response.text
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="uri2ops")
    sub = parser.add_subparsers(dest="cmd", required=True)

    ops = sub.add_parser("operations")
    ops_sub = ops.add_subparsers(dest="action", required=True)
    ops_sub.add_parser("list")
    desc = ops_sub.add_parser("describe")
    desc.add_argument("scheme")
    desc.add_argument("operation")
    ops_sub.add_parser("validate")
    ops.set_defaults(func=operations_cmd)

    reg = sub.add_parser("registry")
    reg_sub = reg.add_subparsers(dest="action", required=True)
    reg_sub.add_parser("list")
    reg_sub.add_parser("validate")
    reg.set_defaults(func=registry_cmd)

    val = sub.add_parser("validate")
    val.add_argument("path")
    val.set_defaults(func=validate_cmd)

    plan = sub.add_parser("plan")
    plan.add_argument("path")
    plan.set_defaults(func=plan_cmd)

    run = sub.add_parser("run")
    run.add_argument("path")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--approve", action="store_true")
    run.add_argument("--adapter", default="auto", choices=["mock", "playwright", "adb", "uia", "auto"])
    run.set_defaults(func=run_cmd)

    serve = sub.add_parser("serve", help="Run uri2ops HTTP daemon with A2A and MCP wrappers")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8791)
    serve.set_defaults(func=serve_cmd)

    env = sub.add_parser("environments", help="List execution environment and operator profiles")
    env_sub = env.add_subparsers(dest="action", required=True)
    env_list = env_sub.add_parser("list", help="Show config/runtime_environments.yaml")
    env_list.add_argument("--root", help="Repo root (defaults to cwd walk-up)")
    env_list.add_argument("--format", choices=["yaml", "json"], default="yaml")
    env_list.set_defaults(func=environments_cmd, action="list")
    env_validate = env_sub.add_parser("validate", help="Validate runtime environment registry")
    env_validate.add_argument("--root", help="Repo root (defaults to cwd walk-up)")
    env_validate.add_argument("--format", choices=["yaml", "json"], default="yaml")
    env_validate.set_defaults(func=environments_cmd, action="validate")

    mcp = sub.add_parser("mcp", help="Call uri2ops MCP tools over HTTP")
    mcp_sub = mcp.add_subparsers(dest="action", required=True)
    call = mcp_sub.add_parser("call", help="POST /mcp/tools/call")
    call.add_argument("tool", help="MCP tool name, e.g. browser_open")
    call.add_argument(
        "--arguments",
        default='{"approve": true}',
        help='JSON object for MCP arguments (default: {"approve": true})',
    )
    call.add_argument(
        "--environment",
        choices=["local", "python", "docker", "mock", "remote"],
        help="Execution environment for browser/desktop ops",
    )
    call.add_argument(
        "--render",
        choices=["text", "ascii", "markdown", "html", "pdf"],
        help="Render browser page results instead of raw JSON",
    )
    call.add_argument("--base-url", default=None, help="uri2ops base URL (defaults from runtime registry)")
    call.add_argument("--timeout", type=float, default=120.0)
    call.add_argument("-o", "--output", help="Write rendered body to file (required for pdf without stdout pipe)")
    call.set_defaults(func=mcp_call_cmd)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
