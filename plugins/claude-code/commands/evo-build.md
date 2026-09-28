---
description: 构建 ontology_v0——读数据、探索 schema、生成 5 类记录
---

## 输入上下文

本命令是触发指令，不是确定性操作；build 的实际执行者是按 skill 行动的 agent。agent 需要
三处输入，均来自当前项目上下文（由调用者提供）：

- **工作区根目录 `<workspace>`**：默认取当前项目的 `.evoontology/`（首次运行自动创建）；
  调用者可用显式的 workspace 绝对路径覆盖，指向别的 ontology workspace。
- **项目上下文**：首次构建时由 skill 确认数据源、workload、Evaluator 和数据边界，并保存到
  `<workspace>/project.json`；后续复用，不重复猜测。
- **允许的工作量（workload）**：Fixed-Split Mode 使用冻结的 construction subset；
  Rolling-Trajectory Mode 使用 seed workload。Builder 不得读取保留验证数据或 ground truth。

本命令中的 `<workspace>` 始终指 Core `resolve_workspace()` 解析后的目录；skill 中出现的
`.evoontology/` 表示这个默认 Workspace，而不是另行拼接的第二个目录。

## 执行

执行 `evo-build` skill（`skills/evo-build/`），构建初始本体层。

按 skill 的 Builder Workflow 执行：Workload-Guided Probing → Evidence-Grounded
Commitment，产出 Term / Mapping / Relation / Constraint / Evidence 五类记录，发布为
`ontology_v0`。

发布通过 `evo-semantic` MCP 的确定性操作完成。`workspace` 一律传当前项目的
`.evoontology/` 绝对路径，不要在本命令中运行 `python -m evoontology...`：

1. `save_version`：把五类记录写入 `versions/ontology_v0/`；
2. `annotate_ontology_version`：保存版本摘要、限制与问题到本体对象的关联；
3. `publish_ontology_build`：校验并激活 `ontology_v0`、初始化进化状态并渲染结果页。
