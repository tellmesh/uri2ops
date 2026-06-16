#!/usr/bin/env bash
# Shared helpers for uri2ops examples.
set -euo pipefail

_uri2ops_examples_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd
}

uri2ops_cmd() {
  if command -v uri2ops >/dev/null 2>&1; then
    uri2ops "$@"
    return
  fi
  local root
  root="$(_uri2ops_examples_root)"
  if [[ -x "$root/.venv/bin/uri2ops" ]]; then
    "$root/.venv/bin/uri2ops" "$@"
    return
  fi
  python -m uri2ops.cli "$@"
}

uri2ops_example_root() {
  _uri2ops_examples_root
}
