<p align="center">
  <a href="README.md">English</a> | 简体中文
</p>

# DDR 集成

本目录包含 DDR 自主分析集成。Runner 支持 MIMIC、10-K 和 GLOBEM 场景 adapter；随附的配置对提供一个具体的 10-K 示例。Baseline 与 semantic 条件使用相同的 Agent 循环、provider 实现、场景输入，以及原生 SQLite/code MCP server。语义配置会额外连接 `tool_server/semantic_mcp.py`，暴露 `browse_semantics` 和 `resolve_semantics`，并读取 `ddr-semantic://session-manifest`。

## 配置

- `configs/baseline.yaml`：使用 benchmark 原生工具，禁用语义访问。
- `configs/ontology.yaml`：保持相同设置，并启用语义 MCP server。

执行前，在本地 DDR 数据安装中设置模型占位符，并更新相对场景路径。凭据从 `DDR_AGENT_API_KEY` 读取；评估凭据可通过 YAML 文件中的字段单独配置。

## Agent 执行

在本目录运行：

```bash
python run_agent.py \
  --scenario 10k \
  --config configs/baseline.yaml \
  --yes

python run_agent.py \
  --scenario 10k \
  --config configs/ontology.yaml \
  --yes
```

随附 YAML 文件定义的是 `10k` 场景，因此应配合 `--scenario 10k` 使用。MIMIC 或 GLOBEM 使用相同字段，并添加对应的场景块。可选参数 `--target-ids`、`--entity-file`、`--parallel` 和 `--log-dir` 支持受限或分布式运行，无需修改 Agent。

语义运行会自动把规范化任务轨迹追加到 `.evoontology/trajectories/`，不会存储 Agent 文本或思维链。

## 评估

```bash
python run_evaluation.py \
  --scenario 10k \
  --config configs/baseline.yaml

python run_evaluation.py \
  --scenario 10k \
  --config configs/ontology.yaml
```

Evaluator 从所选配置读取场景问题文件和对应的 Agent 输出。`--test-mode`、`--parallel` 和 `--output` 可用于本地检查。

## 语义 workspace

仓库不提供预构建 ontology。请针对准备好的 DDR 数据运行 `build-ontology` 以初始化 `.evoontology/`，然后使用语义配置。
