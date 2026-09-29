# EvoOntology 文档

EvoOntology 把「本体层」当作可训练状态，用类似训练神经网络的纪律去演化它——有轮次预算、验证集、
Accept/Reject 门控，但改的是语义记录（Term / Mapping / Relation / Constraint / Evidence），而不是模型权重。

## 文档导航

- [架构总览](architecture.md) —— 闭环、模块划分、两种 mode，以及与 SkillOpt 的架构对照。
- [接入一个新的 Benchmark](guide/new-benchmark.md) —— 用 dataloader / rollout / adapter / config / seed
  skill 五件套接入一个新评测环境（对应 SkillOpt 的 `envs/<name>/` 契约）。
- [使用指南](../USAGE.md) —— 安装、workspace、进化闭环、端到端流程。

## 与 SkillOpt 的对应关系

| SkillOpt | EvoOntology |
| --- | --- |
| Skill 文档（可训练状态） | 本体层 `ontology_vN`（可训练状态） |
| Rollout（目标执行任务） | benchmark 的 `run_agent.py` / `run_evaluation.py` |
| Reflect（优化器产出编辑补丁） | `evolve-ontology` skill 的诊断与归因 |
| Select / Update（learning rate = 最大编辑数） | Candidate 补丁（Content / Tool / Schema） |
| Validation gate | `evoontology.evaluation.EvaluationGate`（GT / LLM Judge） |
| `EnvAdapter` | `evoontology.evolution.EvolutionAdapter`（`evaluate()`） |
| `envs/<name>/` | `benchmarks/<name>/` |
| `configs/<name>/default.yaml` | `benchmarks/<name>/configs/*.yaml` |
| `scripts/train.py` + `_ENV_REGISTRY` | `benchmarks/registry.py` + `python -m benchmarks` |
| `docs/guide/` · `docs/reference/` | 本目录 |
