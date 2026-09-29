<p align="center">
  English | <a href="README.zh-CN.md">简体中文</a>
</p>

# EvoOntology — Claude Code Plugin

The Claude Code plugin packages EvoOntology's three skills—`build-ontology`, `evolve-ontology`, and `explore-ontology`—together with the semantic MCP runtime and a Session Start evolution reminder.

## Components

| Component | Location | Purpose |
| --- | --- | --- |
| Build skill | `skills/build-ontology/` | Build and publish `ontology_v0` |
| Evolve skill | `skills/evolve-ontology/` | Diagnose → attribute → patch → gate |
| Explore skill | `skills/explore-ontology/` | Generate a read-only offline interactive graph |
| MCP configuration | `.mcp.json` | Connect the semantic MCP server automatically with zero configuration |
| Evolution reminder | `hooks/hooks.json` + `scripts/check-reminder.py` | Check `evolution_due` at Session Start |
| Deterministic core | `evoontology/` | Bundled core synchronized from the repository root by `scripts/sync_plugin_core.py` |

The bundled `evoontology/` core supplies the semantic MCP and deterministic store, runtime, trajectory, trigger, evaluation, and evolution capabilities. It stays synchronized with the repository root and makes the plugin self-contained.

## Installation

```bash
claude plugin marketplace add ruc-datalab/EvoOntology
claude plugin marketplace list
claude plugin install evoontology@evoontology
claude plugin list
```

No repository clone, virtual environment, or separate `pip install` is required. `marketplace list` confirms that the Marketplace was added; `plugin install` downloads the plugin; `plugin list` confirms the final installation state. After installation, all three skills, semantic MCP, and the evolution reminder are available.

## Usage

Three namespaced skills are available:

- `/evoontology:build-ontology` — inspect data and schema, generate the five record types, and publish `ontology_v0`.
- `/evoontology:evolve-ontology` — diagnose → attribute → patch → Parent/Candidate gate → persist. Semantic MCP evolution tools such as `start_evolution_run` and `accept_evolution` drive the process. A new run uses a quick two-round or full eight-round default budget. Reject continues within the same run; Accept publishes a new version and advances the checkpoint.
- `/evoontology:explore-ontology` — invoke `visualize_ontology` to generate a read-only offline interactive graph.

The agent follows the corresponding skill for all three entry points; deterministic publication and rendering use semantic MCP tools.

### Two modes

- `fixed_split`: for benchmarks with a fixed question set, ground truth, and official evaluation boundary. The Construction Pool supports construction and diagnosis; the Validation Reserve is used only for the final gate.
- `rolling_trajectory`: for production use or cold starts. A seed workload initializes the ontology layer, and later task trajectories accumulate from the checkpoint. Without ground truth, use independently sampled tasks and an LLM Judge rather than forcing Fold A/B.

Build Step 0 confirms the mode and writes it to `project.json`; Evolve reuses it.

### Semantic MCP

`.mcp.json` launches the semantic service through the bundled cross-platform launcher, and the client starts it automatically. The default workspace is `.evoontology/` in the current project. To select another workspace, append `"--store", "<workspace-root>"` to `args` in `.mcp.json`.

The Data Agent sees the `browse_semantics` and `resolve_semantics` navigation tools and the `evo-semantic://session-manifest` resource. Build, Evolve, and Visualize use `publish_ontology_build`, `finalize_evolution_run`, `visualize_ontology`, and evolution-session tools. Users do not need to run `python -m evoontology...` in their projects.

### Evolution reminder

At every Session Start, `check-reminder.py` reads `<cwd>/.evoontology/state.json` and `trajectories/`. When the default trigger of 30 new tasks or seven days is reached, it injects a reminder; the user decides whether to run `/evoontology:evolve-ontology`. Evolution never starts automatically.

`state.json` uses neutral `checkpoint_time` and `checkpoint_trajectory` fields. The initial baseline is the publication time of `ontology_v0`. Only a formal gate Accept advances the checkpoint; Reject continues in the same run, and Incomplete does not advance it.

## Publication validation

Before `/evoontology:build-ontology` or `/evoontology:evolve-ontology` publishes a version, the agent automatically invokes semantic MCP `validate_semantics`. This deterministic gate checks valid JSON, complete references, and loadability. It does not validate database semantics.
