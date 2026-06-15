#!/usr/bin/env bash
set -euo pipefail
python -m uri2ops.cli validate examples/10_browser_operator/task.health.yaml
python -m uri2ops.cli plan examples/10_browser_operator/task.health.yaml
python -m uri2ops.cli run examples/10_browser_operator/task.health.yaml --adapter mock --approve
