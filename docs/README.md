<p align="center">
  English | <a href="README.zh-CN.md">简体中文</a>
</p>

# EvoOntology Documentation

EvoOntology treats the ontology layer as trainable state and evolves it with discipline similar to neural-network training: bounded rounds, validation data, and Accept/Reject gates. The system edits semantic records—Term, Mapping, Relation, Constraint, and Evidence—not model weights.

## Documentation

- [Architecture overview](architecture.md) — the closed loop, module boundaries, two modes, and an architectural comparison with SkillOpt.
- [Integrating a new benchmark](guide/new-benchmark.md) — connect a new evaluation environment with a dataloader, rollout, adapter, configuration, and seed skill, corresponding to SkillOpt's `envs/<name>/` contract.
- [Product guide](../USAGE.md) — installation, workspace layout, the evolution loop, and an end-to-end workflow.

## Mapping to SkillOpt

| SkillOpt | EvoOntology |
| --- | --- |
| Skill document (trainable state) | Ontology layer `ontology_vN` (trainable state) |
| Rollout (target task execution) | Benchmark `run_agent.py` / `run_evaluation.py` |
| Reflect (optimizer produces an edit patch) | Diagnosis and attribution in the `evolve-ontology` skill |
| Select / Update (learning rate = maximum edits) | Candidate patch across Content / Tool / Schema |
| Validation gate | `evoontology.evaluation.EvaluationGate` (GT / LLM Judge) |
| `EnvAdapter` | `evoontology.evolution.EvolutionAdapter` (`evaluate()`) |
| `envs/<name>/` | `benchmarks/<name>/` |
| `configs/<name>/default.yaml` | `benchmarks/<name>/configs/*.yaml` |
| `scripts/train.py` + `_ENV_REGISTRY` | `benchmarks/registry.py` + `python -m benchmarks` |
| `docs/guide/` · `docs/reference/` | This directory |
