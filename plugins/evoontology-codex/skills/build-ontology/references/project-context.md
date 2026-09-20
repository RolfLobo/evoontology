# EvoOntology Project Context

## Purpose

Project Context stores persistent project-level information shared by Build,
Runtime, and Evolution.

It is created during the initial build and reused by later evolution runs.

The context is stored at:

```text
<project-root>/.evoontology/project.json
```

---

## Fields

```json
{
  "version": 1,
  "mode": "fixed_split | rolling_trajectory",
  "data_source": "...",
  "workload_source": "...",
  "evaluation": {},
  "boundary": {}
}
```

### `mode`

Supported values:

* `fixed_split`
* `rolling_trajectory`

### `data_source`

Location or identifier of the target data environment.

### `workload_source`

For `fixed_split`, the predefined question/workload source.

For `rolling_trajectory`, the seed workload used for initial construction.

### `evaluation`

Fixed-Split example:

```json
{
  "type": "external_evaluator",
  "adapter": "bird",
  "ground_truth_source": "..."
}
```

Rolling-Trajectory example:

```json
{
  "type": "llm_judge"
}
```

Ground Truth may be registered for Evaluator use but MUST NOT be read by
Builder or Evolver.

### `boundary`

Fixed-Split example:

```json
{
  "direction": "A_to_B",
  "evolution_split": "...",
  "validation_split": "...",
  "heldout_split": "..."
}
```

Rolling-Trajectory example:

```json
{
  "strategy": "rolling_trajectory"
}
```

Per-evolution Evolution Pool and Validation Reserve assignments belong to the
evolution record, not `project.json`.

---

## Usage

Build MUST establish and persist Project Context before semantic construction.

Evolve MUST reuse the persisted mode, data sources, and evaluation setup rather
than infer them again.

Project Context does not store:

* active ontology version;
* Task trajectories;
* evolution checkpoints;
* Candidate history.
