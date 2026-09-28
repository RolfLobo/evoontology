"""Trajectory tests: tool-call-level recording, order, and checkpoint queries."""

import pytest

from evoontology import TrajectoryStore, from_message_trace, truncate_result


def _traj(task_id, recorded_at, tool_calls=None):
    return {
        "task_id": task_id,
        "question": f"question for {task_id}",
        "ontology_version": "ontology_v0",
        "tool_calls": tool_calls or [],
        "final_answer": "answer",
        "status": "completed",
        "recorded_at": recorded_at,
    }


def test_append_preserves_tool_calls(tmp_path):
    store = TrajectoryStore(str(tmp_path))
    tool_calls = [
        {"step": 1, "category": "semantic", "tool_name": "browse_semantics",
         "arguments": {"query": "net income"}, "result": {"status": "ok"}, "error": None},
        {"step": 2, "category": "native", "tool_name": "execute_sql",
         "arguments": {"sql": "SELECT 1"}, "result": {"rows": 1}, "error": None},
    ]
    store.append(_traj("task_001", "2026-08-01T00:00:00+00:00", tool_calls))

    loaded = store.load("task_001")
    assert loaded["tool_calls"] == tool_calls
    assert loaded["tool_calls"][0]["category"] == "semantic"
    assert loaded["tool_calls"][1]["category"] == "native"
    assert loaded["tool_calls"][0]["step"] == 1
    assert loaded["tool_calls"][1]["step"] == 2


def test_list_since(tmp_path):
    store = TrajectoryStore(str(tmp_path))
    store.append(_traj("task_001", "2026-08-01T00:00:00+00:00"))
    store.append(_traj("task_002", "2026-08-02T00:00:00+00:00"))
    store.append(_traj("task_003", "2026-08-03T00:00:00+00:00"))

    assert store.count_since(None) == 3
    assert store.count_since("task_001") == 2
    assert store.count_since("task_002") == 1
    assert store.count_since("task_003") == 0


def test_truncate_result_small(tmp_path):
    result = truncate_result({"rows": [1, 2, 3]})
    assert result["result_truncated"] is False


def test_truncate_result_large():
    result = truncate_result("x\n" * 1000)
    assert result["result_truncated"] is True
    assert "result_summary" in result


def test_from_message_trace_separates_semantic_and_native_calls():
    trajectory = from_message_trace(
        task_id="q1",
        question="question",
        ontology_version="ontology_v0",
        messages=[
            {"tool_call": {"tool": "browse_semantics", "arguments": {"query": "x"}}},
            {"tool_result": {"items": []}},
            {"tool_call": {"tool": "execute_query", "arguments": {"sql": "select 1"}}},
            {"tool_result": {"rows": [[1]]}},
            {"role": "agent", "content": "private reasoning must not be stored"},
        ],
        final_answer="select 1",
    )

    assert trajectory["semantic_calls"][0]["tool"] == "browse_semantics"
    assert trajectory["native_tool_calls"][0]["tool"] == "execute_query"
    assert trajectory["final_answer"] == "select 1"
    assert "private reasoning" not in str(trajectory)


def test_append_requires_task_id(tmp_path):
    store = TrajectoryStore(str(tmp_path))
    with pytest.raises(ValueError):
        store.append({"question": "no id"})


@pytest.mark.parametrize("task_id", ["../escape", "..\\escape", "/absolute", ".", ".."])
def test_task_identifiers_must_be_single_path_components(tmp_path, task_id):
    store = TrajectoryStore(str(tmp_path))
    with pytest.raises(ValueError, match="single path component"):
        store.append(_traj(task_id, "2026-08-01T00:00:00+00:00"))
    with pytest.raises(ValueError, match="single path component"):
        store.load(task_id)


def test_task_identifiers_remain_naming_agnostic(tmp_path):
    store = TrajectoryStore(str(tmp_path))
    task_id = "任务 草稿 1"
    store.append(_traj(task_id, "2026-08-01T00:00:00+00:00"))
    assert store.load(task_id)["task_id"] == task_id
