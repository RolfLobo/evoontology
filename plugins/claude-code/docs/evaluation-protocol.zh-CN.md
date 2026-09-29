<p align="center">
  <a href="evaluation-protocol.md">English</a> | 简体中文
</p>

# 评估协议

EvoOntology 的评估按「是否有 ground truth」分两种协议，由系统自动选择（benchmark 提供
Evaluator/GT 时走 GT，否则走 LLM Judge），无需手动声明模式。
两种场景都可能出现 LLM，但角色不同——**有 GT 的 LLM 是 benchmark 的判分器，无 GT 的 LLM
才是 EvoOntology 的裁判**（本文「LLM Judge」专指后者）：

| 维度 | 有 GT（benchmark 判分器） | 无 GT（EvoOntology 裁判） |
| --- | --- | --- |
| 评判对象 | 单个答案 vs GT | Parent 答案 vs Candidate 答案 |
| 判据 | 与 GT 的符合度 | 两个答案的相对优劣 |
| 输入 | `(answer, gt)` | `(question, answer_A, answer_B)` |
| 输出 | `score`（绝对分） | `winner / reason / critical_error` |
| 需不需要 GT | 必须 | 不需要 |
| 匿名 | 不需要 | 必须匿名 A/B |
| 独立性 | 无（benchmark 的事） | 必须独立于 Evolver |
| 谁提供 | benchmark 的评分函数，agent 在 Step 4 调用 | 独立 judge 模型（告诉 agent 其 provider/model/api key，凭据走环境变量），agent 按协议调用 |

**分界点按「是否有 GT」切，不按「是否用 LLM」切**：只要存在 GT 就走绝对评分，`score_fn`
内部是精确匹配还是 LLM 判语义等价是 benchmark 的实现，EvoOntology 只拿分数；只有不存在 GT
时才轮到 EvoOntology 的 LLM Judge。

## 有 GT —— 绝对评分

每个答案相对 GT 打绝对分 `score_fn(answer, gt) -> float`，由 agent 在 evolve skill Step 4
调用 benchmark 的评分函数，聚合 Parent 分数 vs Candidate 分数，比较分数差决定 accept。

## 无 GT —— 相对比较（LLM Judge）

没有客观标尺、无法绝对打分，由 agent 在 Step 4 按协议调用独立 judge 模型（其
provider/model/api key 直接告诉 agent，凭据走环境变量），匿名比较 Parent 与 Candidate 的
答案 `judge_fn(question, answer_A, answer_B) -> verdict`。

**输入**：每个验证任务给 judge `question + answer_A + answer_B`，A/B 随机标记，judge 不知
哪个是 Parent、哪个是 Candidate。

**输出**：

```
{ winner: "A" | "B" | "tie",
  reason: 一句话归因,
  critical_error: bool }
```

**判据**（无 GT 时 judge 无法验证哪个是对的，只能判哪个更合理，引导它看四点）：

1. 是否答对了问题（有无偏题、答非所问）；
2. 结论是否自洽（有无内部矛盾、明显事实错误）；
3. 依据是否可核查（有无给出支撑结论的数据 / 概念 / 计算）；
4. 覆盖度（有无漏掉 question 的关键分析维度）。

`winner` = 综合四点更优的一方；`critical_error` = 出现「错误结论 / 自相矛盾 / 未回答 /
执行失败」等硬伤。

**防偏差**：匿名（A/B 随机标记，消除位置 / 标签偏好）+ 独立（judge 与 Evolver 隔离，不复用
同一模型实例 / 凭据 / 上下文，消除自评偏差）。

**聚合 gate**（门槛故意保守——无 GT 的 judge 信号弱，用强条件弥补）：

对 N 个验证任务统计：`W_c` = Candidate 胜出数、`W_p` = Parent 胜出数、`T` = 平局数、
`E_c` = Candidate 出现 critical_error 的任务数。

```
accept  ⇔  E_c == 0  且  W_c > W_p
否则     →  保留 Parent
```

- `E_c == 0`：Candidate 零硬伤（错误结论 / 自相矛盾 / 未回答 / 执行失败），任一则拒。
- `W_c > W_p`：Candidate 在可判定（非平局）任务上胜出严格多于 Parent；平局不算分，
  平局多时很难满足「严格多于」，自然落在「保留 Parent」。

第一版不叠加 swap 消偏（已匿名）、分维度判、多采样、confidence 字段；「judge 同时看工具
证据」降级为可选（轨迹未存工具调用结果时先只看答案）。
