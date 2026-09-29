<p align="center">
  English | <a href="README.zh-CN.md">简体中文</a>
</p>

# EvoOntology — Codex Plugin

Build an ontology layer from data and analytical goals, validate improvements, and explore concepts, evidence, and execution results. The plugin bundles the deterministic core and MCP, so users do not install a Python package in their projects.

## Three entry points

| Entry point | Purpose |
| --- | --- |
| `$build-ontology` | Prepare questions, build the initial ontology layer, and open the result page |
| `$evolve-ontology` | Collect real tasks, run a missing baseline, validate improvements, and present the result |
| `$explore-ontology` | Explore questions, concepts, evidence, execution results, and version differences at any time |

You can also ask naturally: “Build an ontology layer for this data, focusing on sales analysis,” or “Improve it based on recent use.” Claude Code and Codex share the same Build, Evolve, and Explore workflow names; only invocation syntax follows each platform.

## Installation

```bash
codex plugin marketplace add ruc-datalab/EvoOntology
codex plugin add evoontology-codex@evoontology
codex plugin list
```

Start a new session after installation or an update so the new skills and MCP tools are loaded.

## No question or trajectory files required

Questions expand coverage in this order: current requirements, history from the same data project, then evidence-backed exploratory questions. The host Agent extracts history from accessible context, project records, or user-specified sources; the plugin does not read the account's entire chat history automatically. Without history, the Agent inspects metadata and samples to propose grounded questions. Explicit scope takes precedence, and fixed benchmarks may use only their original construction partition.

`prepare_ontology_workload` preserves provenance, deduplicates questions, and selects by priority and topic coverage. `start_ontology_task` freezes a question and ontology version; `resolve_ontology_task` interprets concepts using that version. SQLite queries can run read-only through `execute_ontology_query` and automatically record real results. Other data environments use host-native tools, then record observed results with `record_ontology_task_event` and persist the trajectory with `finish_ontology_task`. `ontology_workflow_status` reports resumable in-progress tasks.

The plugin never fabricates execution results and cannot obtain complete trajectories from ordinary chat alone.

## Build, evolution, and presentation

Build uses `configure_ontology_project` to create or reuse project settings. After semantic objects and question associations are saved, `publish_ontology_build` validates, activates, initializes state, and opens the result page.

Evolve supports quick, with two rounds, and full, with eight rounds by default. It reuses the project budget unless the user specifies one; both modes use the same evaluation criteria. Resuming a run keeps its frozen budget. Only trustworthy improvements are published; otherwise the current version remains active. `finalize_evolution_run` presents accepted or incomplete results. Presentation failure is reported separately and does not undo publication.

The result page includes a summary, known limitations, linked question and semantic subgraphs, real task outputs, evolution metrics, and public-task replays. Synthetic and real tasks must be reported separately. Successful execution does not imply correctness, and structural change does not imply quality improvement. Formal validation examples are not embedded in the result page, and in-progress validation metrics are not displayed.

`visualize_ontology` generates one offline HTML file at `<workspace>/visualizations/ontology-layer-explorer.html` and opens the browser once by default. In a headless environment, pass `open_browser:false`.

## Modes and data boundaries

- `rolling_trajectory`: production projects or cold starts; accumulate questions and trajectories from requirements and project use.
- `fixed_split`: benchmarks with fixed partitions. Construction supports Build and diagnosis, Validation is used only for the independent gate, and Held-out remains unseen before freezing. Register `construction_question_ids` before importing questions.

Semantic MCP starts through `.mcp.json`. The default workspace is `<project-root>/.evoontology/`. Skill workflows are under `skills/`. The root `evoontology/` package is the sole core source and is synchronized into the plugin with `scripts/sync_plugin_core.py`.

## Codex desktop presentation

For `publish_ontology_build`, `finalize_evolution_run`, and `visualize_ontology`, pass `presentation:"codex"` and `open_browser:false` when the Codex browser panel is available. Open the returned `presentation.browser_url`, or `browser_url` for `visualize_ontology`, with the available `open_in_codex` tool using `target:{type:"browser",url:browser_url}` and `placement:"right"`. Reuse an existing preview tab where possible.

This mode serves only the generated HTML on loopback and does not open an external browser. If the app tool is unavailable, return the working URL and file path without claiming that it opened. Explicit headless requests skip preview startup.
