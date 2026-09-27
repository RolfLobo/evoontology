# EvoOntology — Claude Code Plugin

把 EvoOntology 打包成 Claude Code 插件：提供 `/evo-build`、`/evo-evolve`、`/evo-visualize`
三个命令、builder / evolver 两个 skill、语义 MCP 运行时，以及 Session Start 进化提醒。

## 组件

| 组件 | 位置 | 作用 |
| --- | --- | --- |
| Build 命令 | `commands/evo-build.md` | `/evo-build` 构建 `ontology_v0` |
| Evolve 命令 | `commands/evo-evolve.md` | `/evo-evolve` 触发进化 |
| Visualize 命令 | `commands/evo-visualize.md` | `/evo-visualize` 生成离线交互图 |
| Builder skill | `skills/evo-build/` | 构建初始本体层 |
| Evolver skill | `skills/evo-evolve/` | 诊断 → 归因 → 补丁 → gate |
| MCP 配置 | `.mcp.json` | 语义 MCP server 自动接入（零配置） |
| 进化提醒 | `hooks/hooks.json` + `scripts/check-reminder.py` | Session Start 检查 evolution_due |
| 确定性核心 | `evoontology/` | 内置 core 包（由仓库根经 `scripts/sync_plugin_core.py` 同步） |

语义 MCP 与确定性能力（store / runtime / trajectory / trigger / evaluation /
evolution）由插件内置的 `evoontology/` 核心包提供，与仓库根保持一致（由
`scripts/sync_plugin_core.py` 同步），插件自包含、开箱即用。

## 安装

```bash
claude plugin marketplace add ruc-datalab/EvoOntology
claude plugin marketplace list
claude plugin install evoontology@evoontology
claude plugin list
```

无需 clone 仓库、创建虚拟环境或单独执行 `pip install`。`marketplace list` 用于确认 Marketplace 已添加，
`plugin install` 才会下载插件，`plugin list` 用于确认最终安装状态。安装完成后 build / evolve /
visualize 命令、两个 skill、语义 MCP 与进化提醒自动就位。

## 使用

安装后可用三个命令：

- `/evo-build` —— 读数据、探索 schema、生成五类记录，发布 `ontology_v0`；
- `/evo-evolve` —— 诊断 → 归因 → 补丁 → Parent/Candidate gate → 落地。进化由
  语义 MCP 的进化工具（`start_evolution_run` / `accept_evolution` 等）驱动：新 run 先与用户确认轮数预算（默认 8）与轨迹来源，
  Reject 后在同一 run 内继续下一轮，直到 Accept 发布新版本并推进 checkpoint。
- `/evo-visualize` —— 调用语义 MCP 的 `visualize_ontology` 生成离线交互图，只读不改状态。

`/evo-build` 与 `/evo-evolve` 是触发指令，实际构建 / 进化由 agent 按对应 skill 执行；
确定性发布与渲染统一走语义 MCP 工具。

### 两种 mode

- `fixed_split`：用于已有固定问题集、GT 与官方评测边界的 benchmark；Construction Pool
  用于构建和诊断，Validation Reserve 只用于最终 Gate。
- `rolling_trajectory`：用于真实业务或冷启动；seed workload 初始化本体层，后续按 checkpoint
  收集新 task trajectory。没有 GT 时使用独立任务抽样和 LLM Judge，无需强行划分 Fold A/B。

mode 在 Build Step 0 确认并写入 `project.json`，Evolve 直接复用。

### 语义 MCP

`.mcp.json` 以模块形式 spawn 语义服务，client 自动拉起。默认 workspace 为当前项目的
`.evoontology/`（零配置）；如需指向别的 workspace，在 `.mcp.json` 的 args 里追加
`"--store", "<workspace-root>"`。Data Agent 可见 `browse_semantics`、`resolve_semantics`
两个导航工具与 `evo-semantic://session-manifest` 资源；Build / Evolve / Visualize 通过
`validate_semantics`、`visualize_ontology`、`evolution_status` 与进化会话工具完成，
无需在用户项目中运行 `python -m evoontology...`。

### 进化提醒

每次 Session Start，`check-reminder.py` 读取 `<cwd>/.evoontology/state.json` 与
`trajectories/`，达到触发条件（默认 30 个新 task 或 7 天）时向会话注入提醒，用户自行决定
是否执行 `/evo-evolve`。不自动启动进化。

`state.json` 使用中性的 `checkpoint_time` / `checkpoint_trajectory`：首次基线是
`ontology_v0` 发布时间，只有正式 Gate 的 Accept 才推进 checkpoint（Reject 在
同一 run 内继续循环，Incomplete 不推进）。

## 发布校验（agent 自动）

`/evo-build`、`/evo-evolve` 发布新版本前，agent 会自动调用语义 MCP 的
`validate_semantics` 工具做确定性门禁（JSON 合法 / 引用完整 / 可加载），用户无需手动执行。
只做结构校验，不做数据库语义校验。
