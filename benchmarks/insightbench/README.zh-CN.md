<p align="center">
  <a href="README.md">English</a> | 简体中文
</p>

# InsightBench 集成

本目录包含 InsightBench 分析与评估工作流。两种条件使用相同的问题生成、迭代代码生成 Agent、Python 执行工具、重试策略和 evaluator。启用 `--ontology-layer` 后，Agent 会额外连接 `tool_server/semantic_mcp.py`，读取 `insight-bench-semantic://session-manifest`，并获得两个语义工具。

## 配置与数据

Benchmark flag JSON 和 CSV 文件默认位于 `data/notebooks`。可通过 `--datadir` 指定其他相对路径。Runner 会发现该目录下的所有 `flag-<id>.json` 文件。若要运行特定子集且不随仓库提供数据集划分，请通过 `--flag-ids` 直接传入 ID。

通过 `AGENT_API_KEY` 配置模型访问；需要时使用 `EVAL_API_KEY`。Endpoint 和模型参数也可直接传给 `main.py`。

在本目录安装包和依赖：

```bash
python -m pip install -e .
python -m pip install -r requirements.txt
```

## 执行与评估

在所有可用 flag 文件上运行 baseline 条件：

```bash
python main.py run \
  --datadir data/notebooks \
  --model <model_name>
```

只运行选定 flag：

```bash
python main.py run \
  --datadir data/notebooks \
  --flag-ids 1,2,3 \
  --model <model_name>
```

通过同一入口启用 EvoOntology：

```bash
python main.py run \
  --datadir data/notebooks \
  --model <model_name> \
  --ontology-layer \
  --semantic-store .evoontology \
  --record-trajectories
```

仅在 construction/train workload 上启用 `--record-trajectories`。Held-out evaluation split 必须省略此参数，避免评估条目进入之后的进化输入。

## 语义 workspace

仓库不提供预构建 ontology。在启用语义执行前，对 construction workload 运行 `build-ontology` 以初始化 `.evoontology/`。
