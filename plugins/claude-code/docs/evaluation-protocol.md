<p align="center">
  English | <a href="evaluation-protocol.zh-CN.md">简体中文</a>
</p>

# Evaluation Protocol

EvoOntology selects one of two protocols based on whether ground truth exists. When a benchmark provides an evaluator or ground truth, use GT; otherwise use an LLM Judge. No manual mode declaration is required.

Both paths may involve an LLM, but its role differs: with GT, an LLM may be the benchmark's scorer; without GT, an LLM is EvoOntology's judge. “LLM Judge” below refers only to the latter.

| Dimension | With GT: benchmark scorer | Without GT: EvoOntology judge |
| --- | --- | --- |
| Subject | One answer vs GT | Parent answer vs Candidate answer |
| Criterion | Agreement with GT | Relative quality of two answers |
| Input | `(answer, gt)` | `(question, answer_A, answer_B)` |
| Output | Absolute `score` | `winner / reason / critical_error` |
| Requires GT | Yes | No |
| Anonymous | No | Yes, A/B |
| Independence | Benchmark concern | Must be independent from the Evolver |
| Provider | Benchmark scoring function called by the agent in Step 4 | Independent judge model whose provider, model, and environment-variable credential are supplied to the agent |

The boundary is the presence of GT, not whether an LLM is used. Whenever GT exists, use absolute scoring. Whether `score_fn` performs exact matching or LLM semantic-equivalence judgment is a benchmark implementation detail; EvoOntology consumes only its score. Use EvoOntology's LLM Judge only when GT is absent.

## With GT — absolute scoring

Score every answer against GT with `score_fn(answer, gt) -> float`. In evolve skill Step 4, the agent calls the benchmark scorer, aggregates Parent and Candidate scores, and decides based on the score difference.

## Without GT — relative LLM Judge comparison

Without an objective reference, the agent calls an independent judge model in Step 4. Its provider, model, and API-key environment variable are given directly to the agent. The judge anonymously compares Parent and Candidate answers with `judge_fn(question, answer_A, answer_B) -> verdict`.

**Input**: for each validation task, pass `question + answer_A + answer_B`. Randomize A/B labels so the judge does not know which answer belongs to Parent or Candidate.

**Output**:

```text
{ winner: "A" | "B" | "tie",
  reason: one-sentence attribution,
  critical_error: bool }
```

**Criteria**: without GT, the judge cannot verify objective correctness. It assesses:

1. whether the response answers the question;
2. whether the conclusion is internally consistent and free of obvious factual errors;
3. whether supporting data, concepts, and calculations are verifiable;
4. whether key analytical dimensions of the question are covered.

`winner` is the stronger answer overall. `critical_error` indicates a hard failure such as an incorrect conclusion, internal contradiction, no answer, or execution failure.

**Bias control**: anonymize by randomizing A/B labels to reduce label and position bias. Keep the judge independent from the Evolver by using a separate model instance, credentials, and context.

**Aggregate gate**: because a no-GT judge signal is weak, the gate is deliberately conservative. Across N validation tasks, let `W_c` be Candidate wins, `W_p` Parent wins, `T` ties, and `E_c` Candidate critical errors.

```text
accept  ⇔  E_c == 0 and W_c > W_p
otherwise → retain Parent
```

- `E_c == 0` requires zero Candidate hard failures; any such failure rejects it.
- `W_c > W_p` requires strictly more Candidate wins among non-ties. Ties score nothing, so many ties naturally retain the Parent.

The first release does not add swapped-order judging, dimension-level verdicts, multiple samples, or a confidence field. Supplying tool evidence to the judge is optional when trajectories do not contain tool-call results.
