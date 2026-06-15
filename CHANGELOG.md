# Changelog

## 0.6.0 — 2026-06-15

- Added mock physical operations for robot and device URI planning.
- Operations: `robot://robot/{id}/state`, `move`, `stop`, `mission/{mission_id}/start`.
- Operations: `device://device/{id}/status`, `read`, `write`.
- Example: `examples/36_physical_ops/`.

## 0.5.0 — 2026-06-14

- HTTP daemon: `uri2ops serve` with validate/plan/run endpoints.
- A2A wrapper: `/.well-known/agent-card.json`, `POST /a2a/tasks`.
- MCP wrapper: `GET /mcp/tools`, `POST /mcp/tools/call`.
- Remote operator registry merge via `config/operator_registry.uri.yaml`.
- CLI: `uri2ops registry list|validate`.
- Example: `examples/14_uri2ops_serve/`.

## 0.4.0 — 2026-06-14

- Windows UI Automation adapter with mock and pywinauto (`uia`) backends.
- Operations: `pcwin://window/{id}/focus`, `pcwin://control/{automation_id}/click`.
- Focused window session shared across task steps.
- Example: `examples/13_pcwin_operator/`.
- Optional extra: `pip install -e '.[windows]'`.

## 0.3.0 — 2026-06-14

- Android adapter with mock and ADB + UI Automator backends.
- Operations: `android://device/{id}/screenshot`, `dump_ui`, `tap`.
- Selector-based tap resolves bounds from UI Automator XML dump.
- Example: `examples/12_android_operator/`.

## 0.2.0 — 2026-06-14

- Playwright browser adapter with mock/playwright/auto routing.
- Real `browser://chrome/page/open`, DOM extraction, screenshot, and click handlers.
- Task-scoped Playwright session shared across steps.
- Workflow artifact layout: `artifact://operator/workflows/{task_id}/{run_id}/{step_id}/...`.
- Example: `examples/11_playwright_browser/`.

## 0.1.0 — 2026-06-14

- Initial URI Operation Registry (`registry.yaml` + JSON Schema validation).
- Operator task validate/plan/run CLI.
- Mock browser, assertion, screen, and input adapters.
- Artifact URIs under `artifact://operator/...` with resolver.
- JSONL event log under `output/events/operator/`.
- Payload redaction for `secret=true` fields and sensitive keys.
- Operator policy loading from `config/operator_policy.uri.yaml`.
- Example: `examples/10_browser_operator/task.health.yaml`.
