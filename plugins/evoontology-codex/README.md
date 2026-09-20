# EvoOntology — Codex Plugin

从数据和分析目标出发，构建语义层、验证改进，并查看概念、证据和执行结果。
插件自包含确定性核心和 MCP，不需要在用户项目中安装 Python 包。

## 三个入口

| 入口 | 作用 |
| --- | --- |
| `$build-ontology` | 准备问题、构建初始语义层，完成后自动打开结果页 |
| `$evolve-ontology` | 收集真实任务、运行缺失基线、验证改进，完成后自动展示结果 |
| `$explore-ontology` | 随时浏览问题、概念、证据、执行结果和版本差异 |

也可直接说“为这份数据建立语义层，重点支持销售分析”，或“根据最近的使用情况改进一下”。
旧 `/evo-build`、`/evo-evolve`、`/evo-visualize` 文本触发短语继续路由到新技能；
原生技能 ID 已改名，请在新会话中使用新名称。

## 安装

```bash
codex plugin marketplace add MeiduoChong/EvoOntology
codex plugin add evoontology-codex@evoontology
codex plugin list
```

安装或更新后新建会话，加载新的技能和 MCP 工具。

## 不必准备问题文件或轨迹文件

问题按“本次需求 → 同一数据项目的历史 → 有数据证据的探索问题”补足覆盖。
宿主 Agent 从可访问的当前上下文、项目记录或用户指定来源提取历史；插件不会自动读取
账号全部聊天记录。没有历史时，Agent 探查元数据和样例，提出有依据的问题。
显式限定的问题范围优先，固定 benchmark 仅允许原有 construction 分区。

`prepare_ontology_workload` 保留来源、去重、按优先级和主题覆盖选择问题。
`start_ontology_task` 固定问题和语义版本；`resolve_ontology_task` 按该版本解释概念。
SQLite 可通过 `execute_ontology_query` 只读运行并自动记录真实结果。
其他数据环境使用宿主原生工具，随后通过 `record_ontology_task_event` 记录实际观察，
以 `finish_ontology_task` 持久化轨迹。`ontology_workflow_status` 返回可恢复的运行中任务。
插件不会伪造执行结果，也不会仅凭普通聊天自动获得完整轨迹。

## 构建、进化与展示

Build 使用 `configure_ontology_project` 建立或复用项目设置；保存语义对象和问题关联后，
`publish_ontology_build` 校验、激活、初始化状态并自动打开结果页。
Evolve 支持 quick（2 轮）与 full（默认 8 轮），沿用项目预算或用户明确预算；两档使用
相同评估标准。继续原运行会复用冻结预算。只有可信改善才发布；否则保留当前版本。
`finalize_evolution_run` 展示成功或未完成的结果。展示失败独立报告，不撤销发布。

结果页包含摘要、已知限制、问题与语义子图联动、真实任务输出、进化指标及公开任务回放。
合成任务和真实任务需要分别报告；执行完成不代表正确，结构变化不等于质量改善。
正式验证样例不会嵌入结果页，运行中的验证指标也不会展示。

`visualize_ontology` 生成离线单文件 HTML：
`<workspace>/visualizations/ontology-layer-explorer.html`，默认只打开一次浏览器。
无界面环境可传 `open_browser:false`。

## 模式与数据边界

- `rolling_trajectory`：真实项目或冷启动，从需求和项目使用中积累问题与轨迹。
- `fixed_split`：已有固定分区的 benchmark；Construction 用于构建/诊断，Validation
  仅用于独立门控，Held-out 在冻结前不可见。导入问题前注册 construction_question_ids。

语义 MCP 通过 `.mcp.json` 启动；工作区默认 `<project-root>/.evoontology/`。
技能流程详见 `skills/`；核心以仓库根 `evoontology/` 为唯一来源，使用
`scripts/sync_plugin_core.py` 同步到插件包。

## Codex desktop presentation

For publish_ontology_build, finalize_evolution_run and visualize_ontology, pass
presentation:"codex", open_browser:false when the Codex browser panel is available.
Open the returned presentation.browser_url (or browser_url for visualize_ontology)
with the available open_in_codex tool: target:{type:"browser",url:browser_url},
placement:"right". Reuse an existing preview tab where possible. This mode serves
only the generated HTML on loopback and does not open the external browser.
If the app tool is unavailable, return the working URL and file path without
claiming it opened. Explicit headless requests skip preview startup.
