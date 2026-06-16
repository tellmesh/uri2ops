# TODO — uri2ops

**Version:** 0.5.12 · **Role:** URI Operation Registry + Operator Runtime

> Audyt: 2026-06-16

## v0.1.x

- [x] Operation registry + operator task schema
- [x] Redaction `secret=true` payloads
- [x] Registry schema validation (jsonschema)
- [x] Artifact resolver `artifact://…`
- [x] Policy z `config/operator_policy.uri.yaml`

## v0.2 — browser

- [x] Playwright adapter (`mock` / `playwright` / `auto`)
- [x] `browser://chrome/page/open`, DOM, screenshot

## v0.3 — android

- [x] `adb` + mock: screenshot, dump_ui, tap

## v0.4 — windows

- [x] `uia` + mock: focus, click

## v0.5 — serve

- [x] `uri2ops serve` (A2A + MCP)
- [x] Remote registry merge (`config/operator_registry.uri.yaml`)

## v0.6 — physical + bridge

- [x] Mock `robot://` i `device://`
- [x] **`uri2ops import-graph`** — nl2uri workflow/task → operator task (`operator/graph_bridge.py`)
- [x] Examples: `10`, `12`, `13`, `16`, `36` + `examples/run_all.sh`
- [x] Mapowanie `dom://` → `browser` + `extract_dom` w runner/validator

## Otwarte

- [ ] Real ROS2 adapter za `robot://`
- [ ] Real MQTT/Modbus/OPC UA za `device://`
- [ ] Physical-operation safety policy fixtures (hardware labs)
- [ ] Przykłady voice/desktop gnome w standalone repo (canonical: tellmesh/agents)
