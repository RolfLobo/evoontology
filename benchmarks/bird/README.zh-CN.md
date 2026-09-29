<p align="center">
  <a href="README.md">English</a> | 简体中文
</p>

# BIRD 集成

本目录包含 BIRD text-to-SQL 集成。两种实验条件使用同一个 ReAct Agent 和 SQLite MCP server。语义配置会额外启动 `tool_server/semantic_mcp.py`，向 Agent 提供 `browse_semantics` 和 `resolve_semantics`，并读取 `bird-semantic://session-manifest` 会话文本。

## 配置

- `configs/baseline.yaml`：仅使用 SQLite 工具。
- `configs/ontology.yaml`：使用相同的 Agent 和 SQLite 工具，并增加语义 MCP server。

在所选 YAML 文件中设置模型名称和 provider 字段。凭据从 `BIRD_AGENT_API_KEY` 读取。SQLite 文件位于 `data/mini_dev_data/dev_databases/`；语义 workspace 位于 `.evoontology/<database_id>/`，由 `build-ontology` 创建，不随仓库预置。

## 单问题执行

在本目录运行：

```bash
python run_agent.py \
  --config configs/baseline.yaml \
  --db-path data/mini_dev_data/dev_databases/<database_id>/<database_id>.sqlite \
  --db-id <database_id> \
  --question "<question>"
```

只需切换配置即可启用 EvoOntology：

```bash
python run_agent.py \
  --config configs/ontology.yaml \
  --db-path data/mini_dev_data/dev_databases/<database_id>/<database_id>.sqlite \
  --db-id <database_id> \
  --question "<question>"
```

## 批量评估

`run_evaluation.py` 是基于执行的 BIRD 比较器，而不是独立的模型评估阶段：它生成每条 SQL，在同一个 SQLite 数据库上执行预测 SQL 和对应的 gold SQL，然后报告 EX 和 VES 指标。

```bash
python run_evaluation.py \
  --config configs/baseline.yaml \
  --dataset minidev

python run_evaluation.py \
  --config configs/ontology.yaml \
  --dataset minidev
```

使用 `--split-dir`、`--db-ids`、`--limit` 和 `--output` 适配本地 benchmark 安装。两种条件共用相同的问题加载、并发、重试和结果写入路径。

仅在 construction/train workload 上使用 `--record-trajectories`。它会将规范化且不含思维链的记录写入 `.evoontology/<db_id>/trajectories/`。最终报告使用的 held-out test split 不得启用此参数。

通过同一 wrapper 运行两种条件：

```bash
python scripts/run_full.py --dataset minidev --parallel 8 --limit 10
```

## 语义 workspace

仓库不提供预构建 ontology。`build-ontology` 创建数据库 workspace 后，可运行以下命令验证其 active version：

```bash
python -m evoontology.validate --root .evoontology/<database_id>
```
