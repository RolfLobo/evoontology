<p align="center">
  English | <a href="trajectory-format.zh-CN.md">简体中文</a>
</p>

# Trajectory Format

A trajectory must contain enough detail for evolution diagnosis without unnecessary redundancy. Record at this granularity:

- `semantic_calls`: store **input and result**, so diagnosis can determine what was queried and what matched.
- `native_tool_calls`: store the **complete result up to a limit**. Truncate results beyond roughly 2 KB or 20 lines and set `result_truncated: true`; always provide a stable `result_summary`.
- `ontology_version`: **required**, because attribution must identify the exact version.
- **Do not store chain-of-thought**: the tool I/O sequence is the observable reasoning trace. Chain-of-thought is internal model state, noise, and storage overhead. Material intermediate conclusions belong in `final_answer`; use optional `notes` only when separately needed.

Fields: `task_id / question / ontology_version / semantic_calls / native_tool_calls / final_answer / task_status / errors`. Evaluation results belong under `evolution/`, not in trajectories.

The Data Agent runtime on the benchmark-adapter side appends a trajectory to `trajectories/` after each task. This is not the EvoOntology runtime's responsibility.
