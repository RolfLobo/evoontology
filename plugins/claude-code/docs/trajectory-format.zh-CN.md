<p align="center">
  <a href="trajectory-format.md">English</a> | 简体中文
</p>

# 轨迹格式

轨迹不能太简洁（不够进化诊断用），也不能太复杂（无必要冗余）。记录粒度：

- `semantic_calls`：记 **input + result**（覆盖诊断需要知道「查了什么、命中什么」）。
- `native_tool_calls`：记**完整 result + 上限截断**——`result` 记完整返回，超阈值（约 2KB
  或 20 行）截断并置 `result_truncated: true`；`result_summary` 始终给稳定概览。
- `ontology_version`：**必填**，归因必须关联到具体版本。
- **不记推理过程（CoT）**：工具 I/O 序列本身就是可观察的推理轨迹，CoT 是模型内部状态、
  噪声与存储负担；真正的中间结论已沉淀进 `final_answer`，如需另存可加可选 `notes`。

字段：`task_id / question / ontology_version / semantic_calls / native_tool_calls /
final_answer / task_status / errors`（评估结果不落轨迹，归 `evolution/`）。

轨迹由 Data Agent 运行时（benchmark adapter 侧）在每次任务结束时追加到
`trajectories/`，非 evo 运行时职责。
