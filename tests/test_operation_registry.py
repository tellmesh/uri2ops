from uri2ops.operation_registry.loader import load_operation_registry
from uri2ops.operation_registry.uri_mapping import registry_operation, registry_scheme
from uri2ops.operation_registry.validator import validate_operation_registry


def test_registry_loads():
    reg = load_operation_registry()
    assert reg.get("browser", "open") is not None
    assert reg.get("assertion", "check") is not None


def test_registry_validates():
    assert validate_operation_registry(load_operation_registry()) == []


def test_uri_mapping_normalizes_operator_aliases():
    assert registry_scheme("dom") == "browser"
    assert registry_scheme("browser") == "browser"
    assert registry_operation("dom", "read") == "extract_dom"
    assert registry_operation("screen", "screenshot") == "observe"
    assert registry_operation("robot", "move") == "move"
