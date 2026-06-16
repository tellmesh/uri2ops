#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# shellcheck source=examples/_lib.sh
source "$ROOT/examples/_lib.sh"

FAIL=0
for dir in "$ROOT"/examples/*/; do
  name="$(basename "$dir")"
  [[ "$name" == "_lib.sh" ]] && continue
  script="$dir/run.sh"
  [[ -f "$script" ]] || continue
  echo "===== $name ====="
  if bash "$script"; then
    echo "OK $name"
  else
    echo "FAIL $name" >&2
    FAIL=$((FAIL + 1))
  fi
  echo
done

if [[ "$FAIL" -gt 0 ]]; then
  echo "$FAIL example(s) failed" >&2
  exit 1
fi
echo "All uri2ops examples passed"
