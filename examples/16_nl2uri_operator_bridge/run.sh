#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
# shellcheck source=examples/_lib.sh
source "$ROOT/examples/_lib.sh"

GRAPH="$ROOT/examples/16_nl2uri_operator_bridge/workflow.health.yaml"
TASK="/tmp/weather-operator-task.yaml"

echo "== import-graph (nl2uri workflow -> uri2ops task) =="
uri2ops_cmd import-graph "$GRAPH" --validate --out "$TASK"

echo
echo "== plan =="
uri2ops_cmd plan "$TASK"

echo
echo "== run mock =="
uri2ops_cmd run "$TASK" --adapter mock --approve

if [[ -n "${OPENROUTER_API_KEY:-}" ]] && command -v nl2uri >/dev/null 2>&1; then
  echo
  echo "== optional: nl2uri graph -> import-graph -> run =="
  PROMPT_FILE="$ROOT/../nl2uri/examples/16_llm_graph_planner/prompt.txt"
  if [[ ! -f "$PROMPT_FILE" ]]; then
    PROMPT_FILE="$ROOT/../tellmesh/examples/16_llm_graph_planner/prompt.txt"
  fi
  PROMPT="$(cat "$PROMPT_FILE" 2>/dev/null || echo 'sprawdź health w Chrome')"
  nl2uri graph -p "$PROMPT" --validate > /tmp/nl2uri-workflow.yaml
  uri2ops_cmd import-graph /tmp/nl2uri-workflow.yaml --validate --out /tmp/nl2uri-operator-task.yaml
  uri2ops_cmd run /tmp/nl2uri-operator-task.yaml --adapter mock --approve
else
  echo
  echo "Skipping live nl2uri demo: set OPENROUTER_API_KEY and install nl2uri on PATH"
fi
