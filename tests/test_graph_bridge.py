from __future__ import annotations

from pathlib import Path

import yaml

from uri2ops.operator.graph_bridge import convert_graph_file, graph_to_operator_task, write_operator_task
from uri2ops.operator.runner import run_task
from uri2ops.operator.validator import validate_task_data


WORKFLOW = {
    "nl2uri": {"version": 1, "kind": "workflow_graph"},
    "source_prompt": "wygeneruj agenta pogodowego, uruchom go lokalnie i sprawdź health w Chrome",
    "graph": {
        "id": "weather-health",
        "version": 1,
        "kind": "workflow",
        "description": "Generate weather agent, run locally, verify health",
        "nodes": [
            {
                "id": "generate_weather_domain",
                "uri": "domain://weather-map",
                "operation": "generate",
                "kind": "command",
            },
            {
                "id": "generate_weather_agent",
                "uri": "agent://weather-map-agent",
                "operation": "generate",
                "kind": "command",
                "depends_on": ["generate_weather_domain"],
            },
            {
                "id": "run_weather_agent",
                "uri": "hypervisor://deployment/weather-map-agent.local/run",
                "operation": "run",
                "kind": "command",
                "depends_on": ["generate_weather_agent"],
            },
            {
                "id": "open_health",
                "uri": "browser://chrome/page/open",
                "operation": "open",
                "kind": "command",
                "payload": {"url": "http://localhost:8101/health"},
                "depends_on": ["run_weather_agent"],
            },
            {
                "id": "read_health_dom",
                "uri": "dom://chrome/active/body",
                "operation": "read",
                "kind": "query",
                "depends_on": ["open_health"],
            },
            {
                "id": "verify_ok",
                "uri": "assertion://contains",
                "operation": "check",
                "kind": "assertion",
                "depends_on": ["read_health_dom"],
                "payload": {"actual_from": "read_health_dom.text", "expected": "ok"},
            },
        ],
    },
}


def test_graph_to_operator_task_filters_hypervisor_steps():
    payload, warnings = graph_to_operator_task(WORKFLOW)
    assert payload["task"]["id"] == "weather-health"
    assert [step["id"] for step in payload["steps"]] == ["open_health", "read_health_dom", "verify_ok"]
    assert payload["steps"][0].get("depends_on", []) == []
    assert payload["steps"][1]["operation"] == "extract_dom"
    assert payload["steps"][1]["uri"].startswith("browser://")
    assert payload["steps"][2]["depends_on"] == ["read_health_dom"]
    assert "generate_weather_domain" in payload["skipped_steps"]
    assert any("skipped non-operator" in item for item in warnings)


def test_graph_bridge_validates_and_runs_mock(tmp_path: Path):
    payload, _ = graph_to_operator_task(WORKFLOW)
    assert validate_task_data({"task": payload["task"], "steps": payload["steps"]}) == []
    graph_path = tmp_path / "workflow.yaml"
    graph_path.write_text(yaml.safe_dump(WORKFLOW, sort_keys=False), encoding="utf-8")
    task_path = tmp_path / "operator-task.yaml"
    converted, _ = convert_graph_file(graph_path)
    write_operator_task(converted, task_path)
    from uri2ops.operator.task import load_task

    task = load_task(task_path)
    result = run_task(task, adapter="mock", approve=True, root=tmp_path)
    assert result.ok is True
