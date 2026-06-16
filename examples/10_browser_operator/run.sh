#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
# shellcheck source=examples/_lib.sh
source "$ROOT/examples/_lib.sh"

TASK="examples/10_browser_operator/task.health.yaml"

uri2ops_cmd validate "$TASK"
uri2ops_cmd plan "$TASK"
uri2ops_cmd run "$TASK" --adapter mock --approve
