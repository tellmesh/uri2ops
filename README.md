# uri2ops

`uri2ops` is a standalone **URI Operation Registry + Operator Runtime** package extracted from the larger hypervisor architecture.

Operator adapters live under ``agents/operators/*/adapters/``. The union registry
in ``operation_registry/registry.yaml`` references those modules for CLI use.

```txt
nl2uri -> URI task/workflow graph
uri3   -> URI parsing/routing/validation
uri2ops -> operation registry + operator adapters + execution results
hypervisor -> policy/lifecycle/deployment/audit
```

The key architectural rule:

```txt
Hypervisor does not click, type, or control the OS.
uri2ops executes operator actions through URI-addressed operations.
```

## What is included in v0.1

- URI Operation Registry.
- Operator task schema.
- Mock browser adapter.
- Assertion adapter.
- Screen/input mock adapters.
- Dry-run execution plan.
- Real mock execution with artifacts and JSONL event log.

## v0.2 — Playwright

- Optional Playwright adapter (`--adapter playwright|mock|auto`).
- Real `browser://chrome/page/open`, DOM extraction, screenshot, click.
- Task-scoped browser session shared across steps.
- Workflow artifacts under `artifact://operator/workflows/{task_id}/{run_id}/{step_id}/...`.

## v0.3 — Android

- Android adapter with mock and ADB + UI Automator backends (`--adapter adb|mock|auto`).
- URIs: `android://device/{id}/screenshot`, `dump_ui`, `tap`.
- Tap supports coordinates or selector matched against UI dump XML.

## v0.4 — Windows

- Windows UI Automation adapter with mock and pywinauto backends (`--adapter uia|mock|auto`).
- URIs: `pcwin://window/{id}/focus`, `pcwin://control/{automation_id}/click`.
- Focused window kept in task session for subsequent control clicks.

## v0.5 — Serve + remote registry

- `uri2ops serve --host 127.0.0.1 --port 8791` daemon (FastAPI + uvicorn).
- A2A agent card and `POST /a2a/tasks`.
- MCP-compatible `GET /mcp/tools` and `POST /mcp/tools/call`.
- Remote registry merge from `config/operator_registry.uri.yaml`.

## v0.6 — Physical operations

- Robot/device mock operations for physical-operation planning.
- URIs: `robot://robot/{id}/state`, `move`, `stop`, `mission/{mission_id}/start`.
- URIs: `device://device/{id}/status`, `read`, `write`.
- Real adapters are intentionally not implicit; add `ros2`, `mqtt`, `modbus`,
  `opcua` or vendor SDK adapters behind the same URI contracts.

## CLI

```bash
uri2ops operations list
uri2ops operations describe browser open
uri2ops validate examples/10_browser_operator/task.health.yaml
uri2ops plan examples/10_browser_operator/task.health.yaml
uri2ops run examples/10_browser_operator/task.health.yaml --adapter mock --approve
uri2ops run examples/10_browser_operator/task.health.yaml --adapter playwright --approve
uri2ops run examples/10_browser_operator/task.health.yaml --adapter auto --approve
uri2ops run examples/36_physical_ops/task.robot.yaml --adapter mock --approve
uri2ops run examples/36_physical_ops/task.device.yaml --adapter mock --approve
uri2ops serve --host 127.0.0.1 --port 8791
uri2ops registry list
```

## Why a separate package?

`uri2ops` should remain independent from the hypervisor. The hypervisor can approve, deploy, audit and monitor, but execution details belong here.

## Directory map

```txt
packages/uri2ops/
  uri2ops/
    operation_registry/
    operator/
    schemas/
    server/
  README.md
  CHANGELOG.md
  TODO.md
contracts/proto/operator/
examples/10_browser_operator/
tests/test_uri2ops_*.py
```

## Example task

```yaml
task:
  id: check-agent-health
  description: Open the agent health endpoint and verify OK text.

steps:
  - id: open_health
    uri: browser://chrome/page/open
    operation: open
    kind: command
    payload:
      url: http://localhost:8101/health

  - id: read_dom
    uri: browser://chrome/page/active
    operation: extract_dom
    kind: query
    depends_on:
      - open_health

  - id: verify_ok
    uri: assertion://contains
    operation: check
    kind: query
    payload:
      actual_from: read_dom.text
      expected: ok
    depends_on:
      - read_dom
```

## Links

- [URI Operation Registry](../../docs/URI_OPERATION_REGISTRY.md)
- [Operator Runtime](../../docs/OPERATOR_RUNTIME.md)
- [Security Policy](../../docs/OPERATOR_SECURITY.md)
- [Example 10: Browser Operator](../../examples/10_browser_operator/README.md)
- [CHANGELOG](CHANGELOG.md)
- [TODO](TODO.md)
