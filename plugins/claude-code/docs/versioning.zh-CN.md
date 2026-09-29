<p align="center">
  <a href="versioning.md">English</a> | 简体中文
</p>

# 版本命名与切换

## 版本命名

| 类型 | 命名 | 示例 |
| --- | --- | --- |
| 正式版本 | `ontology_vN`（N 单调递增） | `ontology_v0` 初始、`ontology_v1` 第 1 次 accept |
| 候选 | `vN-cK`（关联源版本 + 序号） | `v0-c1` = 从 v0 进化的第 1 个候选 |

accept 映射：`vN-cK` → `ontology_vN+1`。

读取时兼容迁移前的 `semantic_vN`；新建与 Accept 只使用 `ontology_vN`。

Candidate 在正式 Gate 前保存到 `versions/vN-cK/`，但不得修改 `active.json`。先用
语义 MCP 的 `validate_semantics` 工具（`version` 传 `vN-cK`）校验该未激活版本。

## 切换

「切换版本」是 evolve skill 的操作步骤（改 `active.json` 指针），不设独立命令。
运行时 `store.py` 与命名约定无关：只读 version 字段并加载 `versions/<name>/`，
不校验命名格式。

- Accept：`accept_evolution` 把 Candidate 发布为下一个 `ontology_vN+1`
  （不覆盖已有正式版本），切换 `active.json`，并推进 checkpoint；
- Reject：保留 Parent 为 Active，Candidate 与 `run_N` 轮次记录留作审计，在同一 run
  内继续下一轮，不推进 checkpoint；
- Incomplete：不切换 Active，也不推进 checkpoint。
