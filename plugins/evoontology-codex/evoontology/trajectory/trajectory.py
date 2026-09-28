"""Tool-call-level task trajectory recording.

A trajectory records one Data Agent task: the question, the active ontology
version, every tool call (semantic and native) in execution order, the final
answer, and the task status. Task is the storage/trigger unit; tool call is the
unit Evolver Diagnose/Attribute and the LLM Judge analyze.

Trajectories are appended by the Data Agent runtime (benchmark adapter side)
after each task completes — this module is persistence + query only, not a
recorder that observes the agent.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..workspace import PathLike, resolve_workspace, validate_path_component

# Truncation threshold for oversized tool results (see trajectory-format.md).
_RESULT_MAX_CHARS = 2000
_RESULT_MAX_LINES = 20


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def truncate_result(result: Any) -> Dict[str, Any]:
    """Trim an oversized tool result to a bounded preview + summary.

    Keeps the full result only when small; otherwise stores a truncated preview,
    a ``result_truncated`` flag, and a stable ``result_summary``. Used by the
    Data Agent adapter when recording native tool calls.
    """
    text = str(result)
    lines = text.splitlines()
    too_long = len(text) > _RESULT_MAX_CHARS or len(lines) > _RESULT_MAX_LINES
    if not too_long:
        return {"result": result, "result_truncated": False, "result_summary": text}

    preview = "\n".join(lines[:_RESULT_MAX_LINES])[:_RESULT_MAX_CHARS]
    return {
        "result": preview,
        "result_truncated": True,
        "result_summary": f"{len(lines)} lines, {len(text)} chars; "
        f"preview shows first {_RESULT_MAX_LINES} lines / {_RESULT_MAX_CHARS} chars.",
    }


def from_message_trace(
    *,
    task_id: str,
    question: str,
    ontology_version: str,
    split: str = "",
    messages: List[Dict[str, Any]],
    final_answer: Any = "",
    task_status: str = "completed",
    errors: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """Normalize a benchmark message trace to the trajectory schema.

    Agent prose and chain-of-thought are intentionally not persisted. Only
    observable tool inputs/results and the final answer are retained.
    """
    semantic_calls: List[Dict[str, Any]] = []
    native_tool_calls: List[Dict[str, Any]] = []
    pending_call: Optional[Dict[str, Any]] = None

    for message in messages or []:
        tool_call = message.get("tool_call")
        if isinstance(tool_call, dict) and tool_call.get("tool"):
            pending_call = {
                "tool": str(tool_call["tool"]),
                "input": tool_call.get("arguments", {}),
            }
        if message.get("tool_result") is None or pending_call is None:
            continue
        result = message.get("tool_result")
        call = dict(pending_call)
        if call["tool"] in {"browse_semantics", "resolve_semantics"}:
            call["result"] = result
            semantic_calls.append(call)
        else:
            call.update(truncate_result(result))
            native_tool_calls.append(call)
        pending_call = None

    return {
        "task_id": str(task_id),
        "question": str(question),
        "ontology_version": str(ontology_version),
        "split": str(split),
        "semantic_calls": semantic_calls,
        "native_tool_calls": native_tool_calls,
        "final_answer": final_answer,
        "task_status": str(task_status),
        "errors": list(errors or []),
    }


class TrajectoryStore:
    """Append and query task trajectories under ``<workspace>/trajectories/``."""

    def __init__(self, root: Optional[PathLike] = None):
        self.dir = resolve_workspace(root) / "trajectories"
        self.dir.mkdir(parents=True, exist_ok=True)

    def append(self, trajectory: Dict[str, Any], recorded_at: Optional[str] = None) -> str:
        """Persist one task trajectory to ``trajectories/<task_id>.json``.

        Returns the ``task_id``. An explicit ``recorded_at`` overrides a value
        already present in the trajectory; otherwise the current UTC time is
        used.
        """
        if "task_id" not in trajectory:
            raise ValueError("trajectory requires a 'task_id'")
        task_id = validate_path_component(trajectory["task_id"], label="task_id")
        record = dict(trajectory)
        record["recorded_at"] = recorded_at or record.get("recorded_at") or now_iso()
        self._write(task_id, record)
        return task_id

    def load(self, task_id: str) -> Dict[str, Any]:
        task_id = validate_path_component(task_id, label="task_id")
        path = self.dir / f"{task_id}.json"
        if not path.is_file():
            raise FileNotFoundError(f"Trajectory not found: {task_id}")
        return _load_json(path)

    def list_since(self, since_task_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return trajectories recorded after ``since_task_id`` (exclusive).

        When ``since_task_id`` is None, return all trajectories. Ordering is by
        ``recorded_at``; the checkpoint trajectory's timestamp is the boundary.
        """
        records = self._all()
        if since_task_id is None:
            return records

        checkpoint = None
        for record in records:
            if record.get("task_id") == since_task_id:
                checkpoint = record
                break
        if checkpoint is None:
            return records

        boundary = checkpoint.get("recorded_at", "")
        return [
            r for r in records
            if str(r.get("recorded_at", "")) > boundary
        ]

    def count_since(self, since_task_id: Optional[str] = None) -> int:
        return len(self.list_since(since_task_id))

    def _all(self) -> List[Dict[str, Any]]:
        records = []
        for path in sorted(self.dir.glob("*.json")):
            try:
                records.append(_load_json(path))
            except (json.JSONDecodeError, OSError):
                continue
        records.sort(key=lambda r: str(r.get("recorded_at", "")))
        return records

    def _write(self, task_id: str, record: Dict[str, Any]) -> None:
        task_id = validate_path_component(task_id, label="task_id")
        path = self.dir / f"{task_id}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)
