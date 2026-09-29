<p align="center">
  English | <a href="README.zh-CN.md">简体中文</a>
</p>

# Benchmarks

Three benchmark environments validate the EvoOntology Build → Use → Record → Evolve → Evaluate loop. Each is a self-contained package connected to the evolution loop through an `EvolutionAdapter`, following [SkillOpt](https://github.com/microsoft/SkillOpt)'s `envs/<name>/` contract.

| Environment | Benchmark | Task type | Semantic workspace |
| --- | --- | --- | --- |
| `bird/` | BIRD | Text-to-SQL | One `.evoontology/<db_id>/` per database |
| `ddr_10k/` | DDR-10K | Autonomous data analysis | One `.evoontology/` |
| `insightbench/` | InsightBench | Iterative analysis / code generation | One `.evoontology/` |

## Shared integration contract

A benchmark environment provides four components corresponding to SkillOpt's dataloader, rollout, adapter, and configuration, plus an optional seed skill:

| SkillOpt | EvoOntology | Responsibility |
| --- | --- | --- |
| `dataloader.py` | `data/` or a scenario loader | Load train/validation/test items with IDs from disk |
| `rollout.py` | `run_agent.py` + `run_evaluation.py` | Run the Agent, score each item, and persist results |
| `adapter.py` (`EnvAdapter`) | `evolution_adapter.py` (`EvolutionAdapter`) | Connect the loader and rollout to the evolution lifecycle |
| `configs/<name>/default.yaml` | `configs/baseline.yaml` + `configs/ontology.yaml` | Model, MCP, semantic switch, and evaluation parameters |
| `skills/initial.md` | Plugin `build-ontology` skill | Initial ontology-layer construction method |

The core contract is `evaluate(subject, cases=None, output_hint=None) -> {"metrics", "cases", "artifact_paths"}`. The adapter must use only the standard library; benchmark-heavy dependencies such as the OpenAI SDK, `requests`, and `torch` are used only in `run_agent.py` or `run_evaluation.py` subprocesses.

## Unified discovery

`benchmarks/registry.py` provides lazy-loading registration equivalent to SkillOpt's `_ENV_REGISTRY`:

```bash
python -m benchmarks list           # list registered environments
python -m benchmarks resolve bird   # resolve the BIRD adapter class
```

Construct an adapter in code:

```python
from benchmarks import get

adapter = get("bird")(config_path="configs/ontology.yaml", dataset="minidev")
result = adapter.evaluate(subject="ontology_v0")
```

See [Integrating a new benchmark](../docs/guide/new-benchmark.md).

## Reusing the EvoOntology core

All three benchmarks use the deterministic root `evoontology` package instead of maintaining copies:

| Capability | Module | Integration |
| --- | --- | --- |
| Ontology storage / versioning | `evoontology.ontology.store.SemanticStore` | `save_version` / `publish` / `set_active` |
| Semantic runtime | `evoontology.runtime.runtime.SemanticLayer` | `browse` / `resolve` / `manifest` |
| Semantic MCP | `evoontology.runtime.mcp_server` | `python -m evoontology.runtime.mcp_server --store <workspace>` |
| Trajectory recording | `evoontology.trajectory.TrajectoryStore` | `append` |
| Evolution lifecycle | `evoontology.evolution.EvolutionSession` | Run state machine |
| Evolution adapter | `evoontology.evolution.EvolutionAdapter` | Each benchmark implements `evaluate()` |
| Evaluation orchestration | `evoontology.evaluation.EvaluationGate` | `decide_gt` / `decide_judge` |

Each benchmark directory contains its own Data Agent, native tools, runner, and evaluator. `tceo/` retains benchmark-specific binders, scope, and manifest adapters. Active-version selection and the five-JSON-file gate both use `SemanticStore.load_records()`.

## Data preparation

The repository does not include large raw benchmark datasets, a prebuilt `ontology_v0`, or a prebuilt evolved ontology. Each benchmark README explains its official data setup. After preparation, run `build-ontology` to construct your own ontology. BIRD includes a minimal `formula_1` example—database plus semantic workspace—for offline smoke tests.
