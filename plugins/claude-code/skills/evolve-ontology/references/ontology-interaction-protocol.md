# Semantic Interaction Protocol v1

## Purpose

This protocol defines how an Analysis Agent uses the ontology layer through MCP.

The ontology layer supports:

1. semantic discovery;
2. concept grounding;
3. navigation from analytical needs to database fields.

It does not replace database analysis or produce final conclusions. The Analysis Agent remains responsible for querying data, validating evidence, reasoning, and writing the final output.

---

# Architecture

```text
Analysis Agent
    |
    v
Semantic MCP Server
    |
    v
Ontology Layer Store
```

The Semantic MCP Server provides:

1. a generated Manifest;
2. `browse_semantics`;
3. `resolve_semantics`.

The Manifest explains what is available and how the tools are intended to work together.

The MCP tools provide task-specific semantic discovery and grounding.

---

# Manifest

## Role

The Manifest is an automatically generated tool guide shown to the Analysis Agent when it connects to the Semantic MCP Server.

It provides a concise overview of:

1. the active ontology-layer version;
2. the available semantic tools;
3. the intended relationship between semantic guidance and native data analysis.

The Manifest is a bounded navigation aid. It helps the Agent understand what is available and how to begin, but it does not define the analytical framework or determine the final answer.

## Example

```text
Ontology layer version: ontology_v4
Active constraints: 0

## Semantic MCP Tools

- browse_semantics(query, kind, limit)
  Discover semantic concepts relevant to an analytical need.

- resolve_semantics(mentions, context)
  Resolve selected concepts to database-grounded mappings.

## Suggested Use

Use browse_semantics to discover relevant concepts.
Use resolve_semantics to ground selected concepts in database fields.
Use native analysis tools to query and validate the data.
Use semantic results as guidance, not as final answers.
```

The Manifest should remain concise, reflect the tools that are actually available, and avoid embedding task-specific conclusions or a mandatory analysis workflow.

---

# 1. browse_semantics

## Purpose

Discover semantic objects relevant to the current analytical need.

## Interface

Example input:

```json
{
  "query": "cost factors affecting profitability",
  "kind": "metric",
  "limit": 5
}
```

Example output:

```json
{
  "results": [
    {
      "semantic_id": "labor_cost",
      "type": "metric",
      "name": "Labor Cost",
      "definition": "Employee-related operating expenses"
    }
  ]
}
```

The returned objects support discovery and orientation. They do not by themselves establish database availability or analytical correctness.

---

# 2. resolve_semantics

## Purpose

Resolve selected concepts into database-grounded mappings.

## Interface

Example input:

```json
{
  "mentions": [
    "labor cost"
  ],
  "context": "company profitability analysis"
}
```

Example output:

```json
{
  "results": [
    {
      "semantic_id": "labor_cost",
      "status": "supported",
      "mapping": {
        "table": "financial_statement",
        "column": "labor_expense",
        "fact_name": "labor_cost"
      },
      "constraints": [
        "available after 2018"
      ]
    }
  ]
}
```

The returned mappings help the Agent locate and interpret data. The Agent should still query and validate the underlying database before using them in analysis.

---

# Interaction Flow

The intended interaction is:

1. The Agent receives the Manifest.
2. The Agent uses semantic tools when they add value to the current task.
3. `browse_semantics` supports discovery.
4. `resolve_semantics` supports database grounding.
5. Native data tools provide the evidence used in analysis.
6. The Agent remains responsible for reasoning and the final output.

This is a general interaction pattern rather than a mandatory fixed sequence.

---

# Protocol Principles

## 1. Semantic guidance is not a final answer

The Manifest and semantic tools guide discovery, interpretation, and grounding.

They do not replace evidence collection or final reasoning.

## 2. Semantic information should remain traceable

Semantic results should connect to definitions, mappings, constraints, or supporting evidence in the ontology layer.

## 3. Native data operations remain the evidence source

SQL, database queries, Python, or other native analysis tools should be used to validate data and support analytical claims.

## 4. The initial interaction surface remains simple

The initial protocol consists of:

1. the Manifest;
2. `browse_semantics`;
3. `resolve_semantics`.

Future changes to the Manifest, tools, or interaction pattern should only be introduced when justified by evolution experiments.
