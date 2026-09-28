---
name: evo-evolve
description: This skill is triggered when the user requests to "self-evolve the current ontology layer system". Autonomously evolve an ontology-layer system through a four-step loop of diagnosis, attribution, patching, and Parent/Candidate evaluation until a reproducibly better version is obtained, or external conditions prevent trustworthy continuation.
---

# Self-Evolving Ontology Layer

Continuously improve the ontology-layer system until a credible and
reproducibly better version is obtained.

Evolution operates along three dimensions — **Content, Tool, and Schema**.
When the attributed mechanism involves related prompt, workflow, or runtime
components, they may be modified as part of the corresponding evolution
dimension.

All Candidate changes must be traceable to their target dimension and
reversible to the Parent state.

## Core Principles

* **Discover problems before designing optimization:** Do not only analyze failures that have already appeared. Actively identify analysis needs that the system does not cover, explore, or complete.
* **Evidence before attribution:** Use results, traces, representative tasks, and counterexamples. Do not determine root causes solely from final scores.
* **Determine mechanisms before selecting interventions:** First explain why the system is limited, then let the Agent determine how to optimize it.
* **One Candidate validates one primary hypothesis:** A Candidate may involve multiple components, but all changes must serve the same primary causal mechanism.
* **Validate capability changes before formal evaluation:** First confirm that the intervention truly changes the target capability or analysis behavior.
* **Only a better version counts as completion:** Evolution is successful only when the improvement is credible, reproducible, and has no unacceptable regression.

## Before Evolution

Read:

- `references/project-context.md`;
- `references/ontology-layer-data-boundary.md`;
- previous evolution records and accumulated knowledge, if they exist.

Read the current ontology layer, tools, Builder, runtime flow, and evaluation
setup.

Define the optimization objective, acceptance criteria, and unacceptable
regressions before expensive experiments.

Do not rely only on current conversation context. Reuse persisted project and
evolution state whenever available. If a previous evolution run is still
open, resume it via `resume_evolution_run` instead of starting a new one.

**Stage Output:** A fixed optimization objective and the prior knowledge needed
for evolution.

## Evolution Loop

### Step 0 — Resolve and Freeze Evolution Context

1. Read `.evoontology/project.json`, the current Parent, and the latest
   completed evolution checkpoint.

2. Resolve the data for this evolution run:

   * **Fixed-Split Mode:** reuse the persisted evolution-training and
     validation subsets.

   * **Rolling-Trajectory Mode:** collect eligible Task trajectories after the
     latest checkpoint, freeze the batch, and split it into Evolution Pool and
     Validation Reserve according to
     `references/ontology-layer-data-boundary.md`.

3. Fix the Evaluator and acceptance criteria. For a new run, confirm the
   round budget with the user first (default: 8 rounds); the budget is frozen
   for the run and a resumed run reuses it without asking again.

4. Persist the frozen run context through the MCP tool `start_evolution_run`
   (it writes `evolution/run_N/run.json` with the Parent, adapter, frozen
   budget, and acceptance criteria). Keep the batch's input IDs, validation
   IDs, and Evaluator reference with the run's evaluation setup.

Record IDs only; do not duplicate trajectory files.

If the available data is insufficient for trustworthy evolution and
validation, preserve the Parent and stop without advancing the checkpoint.

**Stage Output:** A reproducible evolution run with fixed Parent, inputs,
validation data, and evaluation protocol.

### Step 1 — Diagnose Problems from Historical Trajectories

Do not rely only on existing failure traces. Analyze both what the system has
done and what it should have done but did not.

Before diagnosing, actively locate the trajectories, evaluation results, and
execution logs relevant to this run and confirm their applicable scope. When
trajectory sources or their scope are not yet settled, confirm them with the
user and persist the confirmed source references for this run:

- Explain each source's path, content scope, time range, and intended use
  before asking for confirmation.
- For a new run, default to the previous run's confirmed source references
  and verify the paths are still valid; re-confirm only when sources are
  added, invalidated, or their scope changes. A resumed run reuses its
  confirmed sources without asking again.
- If no eligible trajectories exist yet, run the Parent on a baseline batch
  first and start diagnosis from its evaluation results, errors, and
  counterexamples.

1. Compare successful, failed, improved, and regressed cases to understand the analysis paths actually taken by the Agent.
2. Examine analysis coverage and identify important dimensions, metrics, concepts, relations, hypotheses, and analysis directions that were ignored, repeatedly missed, or never explored.
3. Examine capability coverage and determine whether the current tool system and its usage loop can support reasonable analysis needs.
4. Examine structural limitations and identify recurring issues showing that the current ontology layer limits exploration, expression, interaction, or evolution.
5. Use representative tasks, counterfactual questions, or exploratory tests to validate potential gaps not exposed in traces.
6. Organize discovered issues into a structured problem map, including:
   * Explicit execution failures;
   * Insufficient analysis coverage;
   * Tool or workflow limitations;
   * System-level structural constraints;
   * Potential gaps requiring further validation.

The problem map should preserve observed symptoms, evidence, causal
hypotheses, and unresolved uncertainty.

**Stage Output:** A problem map covering visible failures, missing capabilities, compensation paths, and potential system limitations.

### Step 2 — Attribute Causal Mechanisms

1. Select high-value problems.
   - Prioritize issues with large impact, repeated occurrence, upstream position, or high uncertainty reduction value.
   - Do not accept a causal explanation simply because a patch is easy to implement.

2. Analyze how each important problem affects the analysis process and final result.

3. Attribute causes to the most relevant part of the ontology layer:

   * **Content:** Whether semantic knowledge is incorrect, incomplete, improperly granular, or insufficiently covered.
   * **Tool:** Whether tool capabilities, interfaces, retrieval, ranking, returned information, or interaction patterns limit usage.
   * **Schema:** Whether the current object model or structural organization cannot reliably support requirements.

4. Determine the nature of each problem:

   * **Existing design error:** Current design produces incorrect behavior;
   * **Missing capability or coverage:** Required knowledge, capability, or coverage is absent;
   * **Structural mismatch:** Current design cannot reliably support analysis requirements.

Do not default to patching existing components. First determine whether the
system is doing something wrong, missing something necessary, or structurally
unsuitable. The optimization approach should follow from this diagnosis and
the available evidence.

5. Generate competing causal explanations and compare them using traces, successful cases, counterexamples, and targeted tests.
6. Separate independent root causes from downstream symptoms.
7. Prioritize causal issues according to expected impact, evidence strength, cross-case reproducibility, and testing value and cost.

Attribution may produce multiple causal explanations. Each should be
independently testable, but the next Candidate should normally target the
highest-priority mechanism.

**Stage Output:** A prioritized set of experimentally testable causal explanations with corresponding evidence and remaining uncertainty.

### Step 3 — Patch the Parent System

1. Select the mechanism currently most valuable to validate.

   Record the primary evolution dimension as Content, Tool, or Schema.

2. Convert the mechanism into a clear, falsifiable hypothesis describing:
   * Current limitation;
   * Why it causes the observed problem;
   * Expected system behavior change if correct;
   * Evidence that supports or falsifies the hypothesis.
3. Design the intervention based on project structure, evidence, and problem characteristics.
   * Prefer solutions that directly test the hypothesis, have clear scope, and are reversible.
   * Do not expand changes unnecessarily or repeatedly apply low-value patches.
4. Keep the primary intervention localized to the attributed Content, Tool, or Schema level.
   * Multiple dependent components may be modified when all changes serve the same primary mechanism.
   * Improvements must not come from permanently disabling, removing, or bypassing the ontology layer.
   * Diagnostic ablation may serve as attribution evidence, not as the final successful solution.
5. Preserve the Parent and record Candidate changes, expected effects, and rollback methods.
6. Run representative cases, targeted replay, or low-cost exploratory experiments to verify that the Candidate changes the intended capability or behavior.
7. Check whether the Candidate introduces new limitations, reduces exploration space, or shifts problems elsewhere.

If the intervention is ineffective, redesign the Candidate. If the
intervention activates but the problem remains, update the attribution. If a
local capability improves without improving the overall process, inspect
integration, side effects, and remaining bottlenecks.

Only proceed to formal comparison after confirming that the target mechanism
has meaningfully changed.

**Stage Output:** One high-value Candidate and evidence showing whether the intended mechanism has activated.

### Step 4 — Evaluate and Gate the Candidate

Compare Parent and Candidate under a controlled and reproducible evaluation
protocol. Evaluate the Candidate as its own stored version; the active
version must not be modified during comparison.

1. Keep inputs, data splits, models, Evaluator, budget, and runtime configuration consistent.

   Evaluate according to the persisted project mode:

   * **Fixed-Split Mode:** compare Parent and Candidate on the frozen validation
     subset using the configured Evaluator.
   * **Rolling-Trajectory Mode:** compare Parent and Candidate on the Validation
     Reserve using the configured LLM Judge.

2. Analyze:
   * Whether target metrics improve;
   * Whether improvement covers the original problem;
   * Whether new regressions or limitations appear;
   * Whether improvement matches the proposed causal mechanism.
3. Determine the Candidate result:
   * **Accept:** the Candidate provides reproducible improvement without
     unacceptable regression;

   * **Reject:** the Candidate does not provide trustworthy improvement,
     including results that are partial or mixed;

   * **Incomplete:** formal evaluation cannot be completed reliably.

Do not accept a Candidate only because a final metric improves. Run the
configured EvaluationGate (GT absolute score or LLM Judge) and Accept only
when it returns accept AND the Candidate shows no unacceptable regression.
When the validation set is small, re-run the evaluation to confirm the
improvement is not single-trial luck. Evaluation should also deepen
understanding of ontology-layer limitations and guide future optimization.

After the decision:

1. Update the problem map and causal understanding.
2. Mark solved problems, remaining limitations, newly discovered issues, and disproven explanations.
3. Preserve the main validated mechanisms, rejected hypotheses, and unresolved uncertainty needed for later rounds.
4. **Accept** — mark the Candidate as accepted and end Candidate search. Proceed to Finalize Evolution Run.
5. **Reject** — record the round through the MCP tool `record_evolution_round`
   (it appends the summary to `evolution/run_N/rounds.jsonl`), update the
   attribution and problem map, then design a new Candidate targeting the
   next most valuable mechanism and repeat Step 1–4. Do not advance the
   checkpoint and do not end the run.
6. **A single Reject never ends the run.** After `record_evolution_round` the
   run remains `running`; you MUST design and evaluate the next Candidate in
   the same run before deciding again. The core refuses `mark_evolution_incomplete`
   for `missing_data`, `unreliable_evaluation`, or `external_block` until at
   least `min_rejects_before_incomplete` (default 2) candidates have been
   rejected. Only `user_interrupted` and `missing_permissions` stop
   immediately; budget exhaustion is raised automatically by
   `begin_evolution_round`.
7. If progress stagnates or similar patches repeat, read `references/exploration-guide.md`, broaden the problem search, and reconsider the current explanation.

Candidate failure, unknown attribution, no-op results, or temporary lack of
effective hypotheses do not indicate completion. They provide information for
the next evolution cycle. Keep iterating until Accept, or until an external
condition (exhausted budget, user interruption, missing data, or unreliable
evaluation) forces an Incomplete stop.

**Stage Output:** A Parent/Candidate decision, updated evolution knowledge, and a clear next direction or rollback point.

### Finalize Evolution Run

A run ends only on Accept or on an external Incomplete stop; a Reject loops
back to a new Candidate within the same frozen batch. The final report must
be based on the session's terminal state and the saved run records, not on
conversation memory.

When the run ends, preserve the evolution record, including:

- frozen run context;
- target evolution dimension and changed components;
- problem map and hypotheses;
- all Candidate changes and their decisions;
- evaluation results;
- final decision;
- unresolved system issues.

In the run records, also capture:

- the target dimension of each round: `content`, `tool`, or `schema`;
- the components actually modified in the round, such as semantic content,
  prompt, workflow, runtime, tool, or schema.

Rejected rounds carry them in their `rounds.jsonl` summary (via
`record_round`); the accepted round carries them in the final run report,
which must be based on `run.json`, `rounds.jsonl`, `trajectory-sources.json`,
and the summaries under `evaluations/`.

If a Candidate was accepted:

1. run `validate_semantics` and `annotate_ontology_version` on the candidate version;
2. `accept_evolution` to publish it as the next `ontology_vN`, switch
   `active.json`, and advance the evolution checkpoint once.

If the run ended Incomplete, do not advance the checkpoint and do not switch
`active.json`; the same batch is retried on the next run.

Call `finalize_evolution_run` after either terminal outcome. It renders the
Results & questions explorer from persisted run state. If rendering fails,
report it separately; the terminal state and active version remain unchanged.

**Stage Output:** Persisted evolution results, updated active version when
accepted, and consistent evolution state.

## Completion Conditions

Only declare success when the final version satisfies:

- the accepted version outperforms the starting Parent under the configured
  evaluation protocol;
- the result is reproducible and evidence-supported;
- no unacceptable regression exists;
- the accepted version can be activated and rerun.

If execution stops due to user interruption or missing permissions, mark
status as `incomplete` immediately. Budget exhaustion is raised by the
session when the budget is spent. For `missing_data` or
`unreliable_evaluation`, the session refuses the stop until at least
`min_rejects_before_incomplete` (default 2) candidates have been rejected.

Preserve the best current version, unresolved causal issues, remaining
hypotheses, and accurate recovery steps.

## Prohibited Actions

Do not improve results by modifying:

- Benchmark questions;
- Ground Truth;
- Labels;
- Evaluator;
- Data splits;
- Acceptance criteria.

Do not hard-code standard answers, task-specific correct values, or expected
Evaluator outputs.

Domain knowledge must be stored in traceable, versioned semantic artifacts
and must not be hidden inside Prompt, Builder code, or orchestration logic.

## Final Deliverable

Report:

* Starting Parent and final best version;
* Comparable experiment results;
* System problem map and prioritized causal mechanisms;
* Accepted and rejected hypotheses;
* Key improvements and regressions;
* Final causal explanation;
* Completion status;
* Reproduction or recovery instructions.

## Research Integrity

Preserve the validity of the benchmark and evaluation protocol. Do not modify benchmark questions, labels, Ground Truth, Evaluator logic, data splits, or acceptance criteria to improve results. Domain knowledge should remain in traceable semantic artifacts rather than being hidden in prompts or orchestration code.
