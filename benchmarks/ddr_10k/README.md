<p align="center">
  English | <a href="README.zh-CN.md">简体中文</a>
</p>

# DDR Integration

This directory contains the DDR autonomous-analysis integration. The runner
supports the MIMIC, 10-K, and GLOBEM scenario adapters; the supplied
configuration pair gives a concrete 10-K example. Baseline and semantic conditions use the
same agent loop, provider implementation, scenario inputs, and native
SQLite/code MCP servers. The semantic configuration additionally connects
`tool_server/semantic_mcp.py`, exposes `browse_semantics` and
`resolve_semantics`, and reads `ddr-semantic://session-manifest`.

## Configuration

- `configs/baseline.yaml`: benchmark-native tools with semantic access
  disabled.
- `configs/ontology.yaml`: the same setup with the semantic MCP server
  enabled.

Before execution, set the model placeholder and update the relative scenario
paths for the local DDR data installation. Credentials are read from
`DDR_AGENT_API_KEY`; evaluation credentials may be configured independently
through the fields in the YAML file.

## Agent execution

Run from this directory:

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

The supplied YAML files define the `10k` scenario, so use `--scenario 10k`
with them. A MIMIC or GLOBEM run uses the same fields with the corresponding
scenario block added. The optional
`--target-ids`, `--entity-file`, `--parallel`, and `--log-dir` arguments
support restricted or distributed runs without changing the agent.

Semantic runs automatically append normalized task trajectories to
`.evoontology/trajectories/`; agent prose/chain-of-thought is not stored.

## Evaluation

```bash
python run_evaluation.py \
  --scenario 10k \
  --config configs/baseline.yaml

python run_evaluation.py \
  --scenario 10k \
  --config configs/ontology.yaml
```

The evaluator reads the scenario question file and corresponding agent
outputs from the selected configuration. `--test-mode`, `--parallel`, and
`--output` may be used for local checks.

## Semantic workspace

The repository does not ship a prebuilt ontology. Run `build-ontology` against the
prepared DDR data to initialize `.evoontology/`, then use the semantic configuration.
