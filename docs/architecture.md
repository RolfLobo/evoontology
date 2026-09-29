<p align="center">
  English | <a href="architecture.zh-CN.md">简体中文</a>
</p>

# Architecture Overview

## Core idea

EvoOntology adopts SkillOpt's methodology: treat the ontology layer as an Agent's trainable state and constrain every change with a round budget, validation data, and an Accept/Reject gate. SkillOpt trains skill documents; EvoOntology evolves ontology-layer records.

```text
Natural-language question ──▶ Data Agent (Claude Code / Codex / benchmark harness)
                                  │ MCP: browse_semantics / resolve_semantics
                                  ▼
                           EvoOntology layer ontology_vN
                                  │
                                  │ evolve-ontology
                                  ▼
             EvolutionSession: freeze budget and data → diagnose → attribute → patch → evaluate
                                  │
                                  ▼
             trajectories/ + evaluations/ → Accept publishes ontology_vN+1
                                           / Reject continues
                                           / Incomplete retains Parent
```

## Modules

| Directory | Responsibility |
| --- | --- |
| `evoontology/` | Deterministic core: ontology store, runtime/MCP, trajectories, triggers, evaluation, evolution state machine, and validation gate |
| `plugins/claude-code/` | Claude Code plugin: `build-ontology` / `evolve-ontology` / `explore-ontology` skills, `.mcp.json`, and a Session Start reminder hook |
| `plugins/evoontology-codex/` | Codex plugin: `AGENTS.md`, the three ontology skills, and `.mcp.json` |
| `benchmarks/` | Three benchmark environments—BIRD, DDR-10K, and InsightBench—each implementing an `EvolutionAdapter` |
| `scripts/` | `sync_plugin_core.py`, which synchronizes the root core into both plugins |
| `docs/` | Architecture and integration documentation |

The core package provides deterministic capabilities only. Build and Evolve intelligence remains in the skills; Python implements the runtime, minimal deterministic validation, and the evolution lifecycle state machine.

## Evolution loop

1. **Build**: `build-ontology` probes the workload, persists evidence, and produces and publishes `ontology_v0`.
2. **Use**: the Data Agent grounds concepts through semantic MCP `browse_semantics` and `resolve_semantics`.
3. **Record**: task trajectories are written to `trajectories/` at Tool Call granularity without chain-of-thought.
4. **Evolve**: after a trigger, `evolve-ontology` loops through diagnosis → attribution → patch → gate inside an `EvolutionSession`.
5. **Evaluate**: `EvaluationGate` compares Parent and Candidate using absolute GT scores or an LLM Judge A/B comparison.

State-machine rules:

```text
running ──Reject──▶ running (next Candidate in the same run)
running ──Accept──▶ accepted (publish, switch active, advance checkpoint)
running ──budget exhausted / external block──▶ incomplete (do not publish or advance)
```

Only Accept or a valid Incomplete state is terminal. Reject supplies input to the next round.

## Two modes

Build Step 0 selects the project's `mode` and writes it to `.evoontology/project.json`:

- **`fixed_split`**: for benchmarks with a fixed question set, ground truth, and evaluation boundary. The Construction Pool supports Build and diagnosis; the Validation Reserve is used only for the final gate and must not flow back into construction, diagnosis, or patch generation.
- **`rolling_trajectory`**: for production use or cold starts without a fixed test set. A seed workload initializes `ontology_v0`; later tasks accumulate in `trajectories/`. After the trigger, a batch is frozen and evaluated with independently sampled tasks or an LLM Judge.

Both modes share the same workspace, versions, and checkpoint mechanism. They differ only in how workloads enter construction, evolution, and evaluation.

## Benchmark integration

Each benchmark is a self-contained environment connected to the evolution loop through an `EvolutionAdapter`, corresponding to SkillOpt's `EnvAdapter`:

- `evolution_adapter.py`: `evaluate(subject, cases, output_hint)` → `{metrics, cases, artifact_paths}`;
- `run_agent.py` / `run_evaluation.py`: rollout and scoring, corresponding to SkillOpt's `rollout.py`;
- `data/` or a scenario loader: dataloader, corresponding to SkillOpt's `dataloader.py`;
- `configs/*.yaml`: baseline and semantic experimental conditions;
- seed skill: the plugin's `build-ontology`, corresponding to SkillOpt's `skills/initial.md`.

Unified discovery uses `benchmarks/registry.py` and `python -m benchmarks`, corresponding to SkillOpt's `_ENV_REGISTRY`. See [Integrating a new benchmark](guide/new-benchmark.md).
