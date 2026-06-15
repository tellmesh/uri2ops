# TODO

## v0.1.x

- [x] Add better redaction for payloads marked `secret=true`.
- [x] Add stricter operation registry schema validation.
- [x] Add artifact resolver compatible with `artifact://...`.
- [x] Add policy file loading from `config/operator_policy.uri.yaml`.

## v0.2

- [x] Add optional Playwright adapter.
- [x] Add real `browser://chrome/page/open` execution.
- [x] Add DOM extraction using Playwright.
- [x] Add screenshot artifact generation.

## v0.3

- [x] Add Android adapter: `adb` + UI Automator.
- [x] Add `android://device/{id}/screenshot`.
- [x] Add `android://device/{id}/dump_ui`.
- [x] Add `android://device/{id}/tap`.

## v0.4

- [x] Add Windows adapter: UI Automation.
- [x] Add `pcwin://window/{id}/focus`.
- [x] Add `pcwin://control/{automation_id}/click`.

## v0.5

- [x] Add `uri2ops serve` daemon mode.
- [x] Add A2A/MCP wrapper.
- [x] Add remote operator registry.

## v0.6

- [x] Add mock `robot://` operations for state, move, stop and mission start.
- [x] Add mock `device://` operations for status, read and write.
- [ ] Add real ROS2 adapter behind `robot://`.
- [ ] Add real MQTT/Modbus/OPC UA adapters behind `device://`.
- [ ] Add physical-operation safety policy fixtures for hardware labs.
