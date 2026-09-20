# Ontology Layer Data Boundary

EvoOntology supports two data-boundary modes:

* `fixed_split`
* `rolling_trajectory`

Candidate-design data and formal-validation data MUST remain separated.

---

## 1. Fixed-Split Mode

Each evaluation dataset is divided into two disjoint and approximately equal-sized
folds, A and B.

For A→B:

```text
Full Dataset
├── Fold A — 50%
└── Fold B — 50%

Fold A
├── 70% Construction / Evolution-Training
└── 30% Evolution-Validation

Fold B
└── Held-out Test
```

The same procedure may be reversed for B→A.

The fold assignment and 70/30 split MUST be frozen before construction.

### Construction / Evolution-Training

May be used to:

* analyze workload requirements;
* explore the data environment;
* build semantic objects;
* collect trajectories;
* diagnose problems;
* design and test Candidates.

### Evolution-Validation

Used only for Parent/Candidate comparison and acceptance.

It MUST NOT be used for:

* diagnosis;
* attribution;
* Candidate design;
* Candidate revision.

### Held-out

Held-out data remains inaccessible until the ontology layer and evolution result
are frozen.

### Ground Truth

Ground Truth, reference answers, labels, and evaluator-internal outputs may only
be accessed by the designated Evaluator.

Builder and Evolver MUST NOT read or use them.

---

## 2. Rolling-Trajectory Mode

### Cold Start

Initial construction uses:

```text
Seed Workload
+
Target Data Environment
```

No Fold A/B or Validation Reserve is required during initial build.

### Evolution Batch

At the start of each evolution run:

1. collect eligible Task trajectories after the latest evolution checkpoint;
2. freeze the current trajectory batch;
3. split it chronologically into:

```text
earlier trajectories
→ Evolution Pool

recent reserved trajectories
→ Validation Reserve
```

The default split is 70% / 30%.

### Evolution Pool

May be used for:

* diagnosis;
* attribution;
* Candidate design;
* targeted replay and exploration;
* Candidate revision.

### Validation Reserve

Used only for formal Parent/Candidate comparison.

It MUST remain inaccessible to Evolver before Candidate evaluation.

For projects without Ground Truth, Parent and Candidate results are compared by
the designated LLM Judge.

Validation questions, Judge rationales, and validation outcomes MUST NOT be
reused for Candidate design.

---

## 3. Common Rules

Builder and Evolver MUST NOT use:

* Ground Truth or reference answers as semantic knowledge;
* reserved validation data for Candidate design;
* held-out data before final freezing;
* evaluator feedback as hidden optimization knowledge.

After an evolution run completes, update the evolution checkpoint so the same
trajectory batch is not reused as a new evolution cycle.

