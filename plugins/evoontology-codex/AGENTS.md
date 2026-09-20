# EvoOntology — Codex Instructions

This project uses EvoOntology: a versioned, self-evolving ontology layer between
natural-language questions and the underlying data. The deterministic core lives
in the `evoontology` Python package; the Build/Evolve method lives in the shared
skills bundled in this plugin's `skills/` directory.

The `evo-semantic` MCP server is already running with the bundled core. Drive all
deterministic build/evolve/visualize operations through its tools with an explicit
`workspace` argument (the absolute path to `<project-root>/.evoontology`). Do not
run `python -m evoontology...` or `from evoontology import ...` from the user
project — the core is not installed there in a plugin-only setup.

## Entry points

- **Build** — when the user asks to "build the ontology" or runs `/build-ontology`,
  execute the `build-ontology` skill (see
  `skills/build-ontology/SKILL.md`). Use the MCP tools `save_version`,
  `annotate_ontology_version` and `publish_ontology_build` to publish
  `ontology_v0` and initialize the trigger checkpoint.
- **Evolve** — when the user asks to "evolve the ontology" or runs `/evolve-ontology`,
  execute the `evolve-ontology` skill (see
  `skills/evolve-ontology/SKILL.md`) following
  Diagnose → Attribute → Patch → Evaluate/Gate. Drive the loop with the MCP
  tools `start_evolution_run` / `resume_evolution_run`, `begin_evolution_round`,
  `save_version`, `record_evolution_evaluation`, `record_evolution_round`,
  `accept_evolution`, and `mark_evolution_incomplete`. Resume an existing
  session when one is running, reuse requested or saved budgets and announce the quick/full budget when
  creating a new run, and evaluate Candidates on independent versions without
  switching `active.json`. Only an accepted Candidate is published as the next
  `ontology_vN`, switches `active.json`, and advances the checkpoint; an
  Incomplete run changes neither.

- **Explore** — when the user asks to "explore the ontology", "visualize the ontology" or runs
  `/explore-ontology` (or `$explore-ontology`), execute the `explore-ontology` skill (see
  `skills/explore-ontology/SKILL.md`) and call the MCP tool `visualize_ontology`
  to render the active (or an explicitly requested) version as a standalone
  offline multi-version HTML at `<resolved-workspace>/visualizations/ontology-layer-explorer.html`,
  read-only. For this tool, a project root or `.evoontology` container may resolve
  to one nested database workspace; ambiguous candidates require an exact path.

For Codex, the slash-style phrases above are aliases that route to the matching
skills. The native Codex skill invocations are `$build-ontology`, `$evolve-ontology`, and
`$explore-ontology`.

## Semantic MCP tools

The `evo-semantic` MCP server exposes two bounded navigation tools plus a
session manifest resource:

- `browse_semantics(query, kind, limit)` — discover concepts relevant to a need;
- `resolve_semantics(mentions, context)` — resolve concepts to grounded
  mappings, relations, constraints, and evidence.

Use them to ground analytical concepts before querying real data with native
tools. They are guidance, not final answers.

The same server also exposes the deterministic build/evolve operations
(`validate_semantics`, `visualize_ontology`, `evolution_status`, version
helpers, and the evolution-session tools). Use those for the workflows above.

## Evolution reminder

Before a session, check whether evolution is due by calling the MCP tool
`evolution_status` with `workspace` set to `<project-root>/.evoontology`.

If `check.evolution_due` is true, remind the user that `/evolve-ontology` is
available. Never start evolution automatically.

## Low-friction workload and delivery

Use supplied analytical needs, relevant same-data project history, then grounded
exploration questions to fill gaps. Question files and pre-existing trajectories
are optional. Follow the shared workload-experience reference in Build/Evolve.
Never infer access to global chat history. Preserve explicit user scope and fixed
benchmark boundaries. Missing business definitions stay limitations.

For a requested data task using this ontology, record actual observations through
start_ontology_task / record_ontology_task_event / finish_ontology_task; use
resolve_ontology_task for a pinned version and execute_ontology_query for built-in
read-only SQLite execution. Other data environments use the host's native tools.
Record observable calls and outputs, not hidden reasoning. Check
ontology_workflow_status to resume interrupted work. Ordinary tool use alone does
not automatically create complete trajectories; finish the task record explicitly.

Build ends with publish_ontology_build; Evolve ends with finalize_evolution_run.
Both automatically render/open the outcome explorer once. Rendering failure does
not invalidate publication. Explore is always available for read-only inspection.

Legacy phrases /evo-build, /evo-evolve and /evo-visualize route respectively to
build-ontology, evolve-ontology and explore-ontology. The old native skill IDs have
been renamed; use the new $ names in fresh sessions.

## Codex desktop presentation

For publish_ontology_build, finalize_evolution_run and visualize_ontology, pass
presentation:"codex", open_browser:false when the Codex browser panel is available.
Open the returned presentation.browser_url (or browser_url for visualize_ontology)
with the available open_in_codex tool: target:{type:"browser",url:browser_url},
placement:"right". Reuse an existing preview tab where possible. This mode serves
only the generated HTML on loopback and does not open the external browser.
If the app tool is unavailable, return the working URL and file path without
claiming it opened. Explicit headless requests skip preview startup.
