# BIRD Integration

This directory contains the BIRD text-to-SQL integration. Both experimental
conditions use the same ReAct agent and SQLite MCP server. The semantic
configuration additionally starts `tool_server/semantic_mcp.py`, makes
`browse_semantics` and `resolve_semantics` available to the agent, and reads
the session text at `bird-semantic://session-manifest`.

## Configuration

- `configs/baseline.yaml`: SQLite tools only.
- `configs/ontology.yaml`: the same agent and SQLite tools, plus the semantic
  MCP server.

Set the model name and provider fields in the selected YAML file. Credentials
are read from `BIRD_AGENT_API_KEY`. SQLite files live under
`data/mini_dev_data/dev_databases/`; semantic workspaces live under
`.evoontology/<database_id>/` and are created by `build-ontology` rather than shipped prebuilt.

## Single-question execution

Run from this directory:

```bash
python run_agent.py \
  --config configs/baseline.yaml \
  --db-path data/mini_dev_data/dev_databases/<database_id>/<database_id>.sqlite \
  --db-id <database_id> \
  --question "<question>"
```

Enable EvoOntology by changing only the configuration:

```bash
python run_agent.py \
  --config configs/ontology.yaml \
  --db-path data/mini_dev_data/dev_databases/<database_id>/<database_id>.sqlite \
  --db-id <database_id> \
  --question "<question>"
```

## Batch evaluation

`run_evaluation.py` is the BIRD execution-based comparator, not a separate
model-based evaluation stage: it generates each SQL query, executes it and
the corresponding gold SQL against the same SQLite database, then reports EX
and VES metrics.

```bash
python run_evaluation.py \
  --config configs/baseline.yaml \
  --dataset minidev

python run_evaluation.py \
  --config configs/ontology.yaml \
  --dataset minidev
```

Use `--split-dir`, `--db-ids`, `--limit`, and `--output` to adapt the command
to a local benchmark installation. The evaluation runner uses the same
question loading, concurrency, retry, and result-writing path for both
conditions.

Use `--record-trajectories` only on the construction/train workload. It writes
normalized, chain-of-thought-free records to
`.evoontology/<db_id>/trajectories/`. Do not enable it on the held-out test
split used for final reporting.

Run both conditions through the same wrapper:

```bash
python scripts/run_full.py --dataset minidev --parallel 8 --limit 10
```

## Semantic workspace

The repository does not ship a prebuilt ontology. After `build-ontology` creates a
database workspace, validate its active version with:

```bash
python -m evoontology.validate --root .evoontology/<database_id>
```
