# Example 16 — nl2uri graph → uri2ops task

`nl2uri` plans multi-scheme workflows (domain, agent, hypervisor, browser, assertion).
`uri2ops` executes only operator steps (browser, dom, assertion, screen, input, android, pcwin, robot, device).

This example converts a full workflow graph into an operator task and runs the browser/assertion slice with mock adapters.

```bash
uri2ops import-graph examples/16_nl2uri_operator_bridge/workflow.health.yaml --validate --out /tmp/task.yaml
uri2ops plan /tmp/task.yaml
uri2ops run /tmp/task.yaml --adapter mock --approve
```

End-to-end with nl2uri (optional, requires `OPENROUTER_API_KEY` or rule-based fallback):

```bash
nl2uri graph -p "$(cat ../nl2uri/examples/16_llm_graph_planner/prompt.txt)" --validate > /tmp/workflow.yaml
uri2ops import-graph /tmp/workflow.yaml --validate --out /tmp/task.yaml
uri2ops run /tmp/task.yaml --adapter mock --approve
```

Hypervisor/domain/agent steps are listed in `skipped_steps` and omitted from execution.
