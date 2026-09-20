---
name: build-ontology
description: Build an initial ontology from data and analytical goals, prepare relevant questions from supplied needs and project history, and automatically show the evidence-grounded result.
---

# Build Ontology Layer

Construct the first version of an ontology layer for a target workload.

The goal is to discover reusable, evidence-grounded analytical knowledge
from questions and data-environment exploration.

The semantic schema defines the structure of the ontology layer.
The Builder Agent discovers and populates semantic content under this
schema.

---

# Before Starting

Read:

- references/ontology-schema.md
- references/ontology-interaction-protocol.md
- references/ontology-layer-data-boundary.md
- references/project-context.md
- references/workload-experience.md

The generated ontology layer MUST follow ontology-schema.md.

The semantic interaction assumptions MUST follow
ontology-interaction-protocol.md.

Do not create alternative semantic object structures.

All dataset access, split usage, freezing, and evaluation boundaries MUST
follow ontology-layer-data-boundary.md.

---

# Builder Workflow

## Step 0 — Initialize Build Context

Before construction, establish the project context and data boundary.

If an active semantic version already exists, do not rebuild or overwrite it. Direct the user to evolution unless they explicitly request a new workspace or destructive reinitialization.
### 1. Resolve context

If `.evoontology/project.json` exists, load and reuse the persisted project
context. Do not re-infer or overwrite it unless the user explicitly requests
reconfiguration.

Otherwise, determine the project mode:

- **Fixed-Split Mode:** a predefined dataset split and external Evaluator are
  available.
- **Rolling-Trajectory Mode:** the ontology layer is initialized from a seed
  workload and later evolves from accumulated Task trajectories.

Resolve the target data source and analytical goal. Use the workload preparation
workflow in references/workload-experience.md: supplied questions, relevant
project history, then evidence-grounded generated questions to fill coverage gaps.
A user-provided question file is optional. Resolve the workload source and Evaluator. When Ground
Truth exists, register its location for Evaluator use only; Builder and Evolver
must not read it.

### 2. Establish data boundary

For **Fixed-Split Mode**:

- create or load the frozen split defined by
  `references/ontology-layer-data-boundary.md`;
- identify the evolution-training, validation, and held-out subsets;
- expose only the permitted construction/evolution workload to the Builder.

For **Rolling-Trajectory Mode**:

- use the resolved seed workload and target data environment for initial
  construction;
- do not create Fold A/B or a validation reserve during initial build.

### 3. Confirm and persist

Present a concise summary of the data source, analytical scope and evaluation
boundary. Reuse explicit authorization already in the request; ask only when a
material source or business-definition ambiguity remains. Persist context using
configure_ontology_project. Do not require users to choose internal mode names.
Later evolution runs must reuse this context rather than infer it again.

**Stage Output:** A resolved and persisted project context and data boundary.

## Step 1 — Workload-Guided Probing

### Understand workload requirements

Read only the workload permitted by the persisted project boundary: the frozen construction split in Fixed-Split Mode, or the seed workload in Rolling-Trajectory Mode.

Identify:

- recurring analytical dimensions;
- concepts and metrics required for reasoning;
- relationships needed between concepts;
- evidence required to answer questions reliably.

Create a workload coverage map.

The coverage map is a construction artifact, not part of the semantic
layer. Its purpose is to ensure important analytical requirements are not
lost during ontology layer construction.

Start semantic construction from analytical requirements. In a cold start,
metadata inspection may first help propose grounded analytical questions; it must
not turn physical table structure into unsupported business semantics.

### Design semantic requirements

Translate workload requirements into semantic objects defined by
ontology-schema.md.

Determine:

- required Terms;
- required Mappings;
- useful Relations using one of the five controlled `relation_type` values
  defined in ontology-schema.md: association / hierarchy / composition /
  equivalence / derivation;
- necessary Constraints.

For each Relation, classify the relationship type using the decision
priority defined in ontology-schema.md. Do not use free-text types such as
`affects` or `belongs_to`.

Keep the ontology layer minimal and reusable. Do not create objects without
a clear workload purpose.

### Explore data-environment evidence

Use available read-only tools to inspect the target data environment,
including databases, structured files, documents, metadata, and other
supported data sources.

For each semantic requirement:

- identify plausible candidate data sources, structures, and elements based
  on structural metadata, relationships, workload terms, and representative
  content;
- inspect and compare candidates' granularity, identifiers, fields,
  relationships, metadata, and representative content;
- do not stop at the first plausible match when multiple candidates remain
  semantically possible;
- stop candidate expansion when remaining candidates lack support from the
  workload, data structure, metadata, representative values, or observed
  content;
- verify the selected grounding's meaning, scope, and granularity;
- record supporting evidence, including why competing candidates were not
  selected when the distinction is analytically important.

Semantic objects must be grounded in reproducible observations from the
target data environment. Do not infer unsupported concepts from external
knowledge.

When multiple data sources or elements are plausible groundings for the same
analytical concept, document their distinct semantic roles, granularity,
scope, and applicability conditions.

Use Mapping to connect analytical concepts to concrete data sources,
structures, or elements. Use Constraint to record data-grounded applicability
conditions, value interpretations, and business rules. Use Relation to record
semantic connections between Terms. Use Evidence to record the reproducible
observations supporting these semantic claims.

**Stage Output:** Candidate semantic objects and their data-grounded evidence.

---

## Step 2 — Evidence-Grounded Commitment

### Generate ontology layer

Create semantic objects according to ontology-schema.md:

- Term;
- Mapping;
- Relation;
- Constraint;
- Evidence.

Every active semantic object must be traceable to:

- a workload requirement;
- data-environment evidence.

The ontology layer should preserve the workload coverage map while storing
only validated semantic knowledge.

Semantic objects MUST contain only the fields defined in
ontology-schema.md. Do not add query-generation instructions, SQL templates,
procedural reasoning steps, or task-specific solution strategies. Do not
encode such prohibited content inside schema-defined free-text fields as a
workaround.

Relation objects MUST use one of the five controlled `relation_type` values.
Describe the connection semantically rather than as a query template.

Constraint objects MUST include suitable `trigger_keywords` so that relevant
constraints can be discovered at runtime.

### Validate ontology layer

Validate that:

- each important analytical dimension in the workload coverage map is
  represented by grounded semantic objects where valid grounding exists;
- Mappings correspond to real data structures;
- Relations and Constraints make required semantic relationships,
  applicability conditions, value interpretations, or business definitions
  explicit;
- Evidence can be reproduced;
- semantic objects can be accessed through the semantic interaction protocol;
- semantic objects contain only schema-defined fields.

Coverage validation confirms semantic availability and grounding; it does
not by itself guarantee successful task execution.

If no valid grounding exists, record a coverage gap or known limitation. Do
not fabricate semantic objects.

Revise unsupported, ambiguous, incomplete, or schema-invalid objects.

### Publish

Publish the initial ontology-layer version with:

- semantic objects and evidence;
- known limitations;
- build metadata;
- project mode and data-boundary metadata;
- split identifier when using Fixed-Split Mode;
- seed-workload source when using Rolling-Trajectory Mode.

Complete publication through the `evo-semantic` MCP tools (pass the absolute
`.evoontology/` path as `workspace`; do not run `python -m evoontology...`) in
this order:

1. `save_version` — write `ontology_v0`'s five record files;
2. `annotate_ontology_version` — save a summary, limitations and question-to-object links;
3. `publish_ontology_build` — validate, activate, initialize evolution state and
   automatically render/open the Results & questions explorer.

If the user requests task demonstrations, run representative public questions
through the task recording tools and refresh visualize_ontology afterward. Do not
present structural validation as proof of task accuracy. On presentation failure,
report the successful publication and retry rendering; do not rebuild the ontology.

Initial build is not an evolution run. Evolution-history fields such as
`last_evolution_trajectory` and `last_evolution_time` must remain unset until
the first evolution run completes.

**Stage Output:** An activated initial ontology layer with initialized
evolution-trigger state.

## Codex desktop presentation

For publish_ontology_build, finalize_evolution_run and visualize_ontology, pass
presentation:"codex", open_browser:false when the Codex browser panel is available.
Open the returned presentation.browser_url (or browser_url for visualize_ontology)
with the available open_in_codex tool: target:{type:"browser",url:browser_url},
placement:"right". Reuse an existing preview tab where possible. This mode serves
only the generated HTML on loopback and does not open the external browser.
If the app tool is unavailable, return the working URL and file path without
claiming it opened. Explicit headless requests skip preview startup.
