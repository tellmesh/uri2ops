# Example 10 — Browser Operator Mock

This example validates and executes a simple browser-like workflow using the mock adapter.

```bash
uri2ops validate examples/10_browser_operator/task.health.yaml
uri2ops plan examples/10_browser_operator/task.health.yaml
uri2ops run examples/10_browser_operator/task.health.yaml --dry-run
uri2ops run examples/10_browser_operator/task.health.yaml --adapter mock --approve
```

The mock adapter does not start Chrome. It returns deterministic results and writes artifacts/events under `output/`.
