<p align="center">
  English | <a href="README.zh-CN.md">简体中文</a>
</p>

# InsightBench Integration

This directory contains the InsightBench analysis and evaluation workflow.
Both conditions use the same question generation, iterative code-generation
agent, Python execution tool, retry policy, and evaluator. With
`--ontology-layer`, the agent additionally connects to
`tool_server/semantic_mcp.py`, reads
`insight-bench-semantic://session-manifest`, and receives the two semantic tools.

## Configuration and data

Benchmark flag JSON and CSV files are expected under `data/notebooks` by
default. Another relative location can be supplied with `--datadir`. The
runner discovers every `flag-<id>.json` file in that directory. To run a
specific subset without shipping a dataset partition, pass the IDs directly
with `--flag-ids`.

Set model access through `AGENT_API_KEY` and, when required, `EVAL_API_KEY`;
endpoint and model arguments can also be supplied directly to `main.py`.

Install the package and dependencies from this directory:

```bash
python -m pip install -e .
python -m pip install -r requirements.txt
```

## Execution and evaluation

Run the baseline condition over all available flag files:

```bash
python main.py run \
  --datadir data/notebooks \
  --model <model_name>
```

Run selected flags only:

```bash
python main.py run \
  --datadir data/notebooks \
  --flag-ids 1,2,3 \
  --model <model_name>
```

Enable EvoOntology through the same entry point:

```bash
python main.py run \
  --datadir data/notebooks \
  --model <model_name> \
  --ontology-layer \
  --semantic-store .evoontology \
  --record-trajectories
```

Enable `--record-trajectories` only for construction/train workloads. Omit it
for the held-out evaluation split so evaluation items cannot enter later
evolution input.

## Semantic workspace

The repository does not ship a prebuilt ontology. Run `build-ontology` over the
construction workload to initialize `.evoontology/` before enabling semantic execution.
