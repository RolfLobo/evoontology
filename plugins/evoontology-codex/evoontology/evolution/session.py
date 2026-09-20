"""EvolutionSession: lifecycle state machine for one evolution run.

The Skill decides *why* and *what* to change; the session guarantees the run
cannot end incorrectly. State rules::

    running -- Reject -----------------> running (next round)
    running -- Accept -----------------> accepted
    running -- budget/external block --> incomplete

Reject, a missing hypothesis, or a single finished experiment never complete
the run. Only Accept or a legitimate Incomplete stop are terminal.

Persisted under ``<workspace>/evolution/<run_id>/``:

- ``run.json`` — status, Parent, current Candidate, round, frozen budget;
- ``trajectory-sources.json`` — user-confirmed trajectory source references;
- ``rounds.jsonl`` — one summary line per finished round;
- ``evaluations/`` — stable summaries of formal Parent/Candidate evaluations.
"""

from __future__ import annotations

import json
import re
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..ontology.store import SemanticStore
from ..trigger.trigger import EvolutionTrigger
from ..workspace import PathLike, ensure_workspace, load_project, resolve_workspace
from .adapter import normalize_result
from ..evaluation.evaluation import EvaluationGate
from ..validate import validate

RUNNING = "running"
ACCEPTED = "accepted"
INCOMPLETE = "incomplete"

TERMINAL_STATES = frozenset({ACCEPTED, INCOMPLETE})
DEFAULT_MAX_ROUNDS = 8
DEFAULT_MIN_REJECTS_BEFORE_INCOMPLETE = 2
RUN_SCHEMA_VERSION = 1

#: Legitimate external-stop reasons for an ``incomplete`` run.
INCOMPLETE_REASONS = frozenset(
    {
        "budget_exhausted",
        "user_interrupted",
        "missing_data",
        "missing_permissions",
        "unreliable_evaluation",
        "external_block",
    }
)

_RUN_DIR_RE = re.compile(r"^run_(\d+)$")
# Legacy ``semantic_vN`` directories remain readable during migration, while
# every automatically published version uses the canonical ``ontology_vN``.
_OFFICIAL_VERSION_RE = re.compile(r"^(?:ontology|semantic)_v(\d+)$")


class EvolutionError(RuntimeError):
    """Raised when an evolution lifecycle rule would be violated."""


class EvolutionBudgetExhausted(EvolutionError):
    """Raised when a new round is requested but the frozen budget is spent."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json_atomic(path: Path, data: Dict[str, Any]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


class EvolutionSession:
    """State, budget, and publication control for a single evolution run."""

    def __init__(
        self,
        workspace: Optional[PathLike] = None,
        *,
        project_root: Optional[PathLike] = None,
    ):
        self.workspace = resolve_workspace(workspace, project_root=project_root)
        self._run: Optional[Dict[str, Any]] = None

    # ---- run lifecycle -----------------------------------------------------

    def start_run(
        self,
        parent_version: str,
        *,
        adapter: str = "",
        max_rounds: Optional[int] = None,
        acceptance: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new run with a frozen, user-confirmed round budget.

        Budget priority: explicit ``max_rounds`` > optional project setting >
        default 8. The caller (Skill) must have confirmed the budget with the
        user before invoking this.
        """
        if not str(parent_version or "").strip():
            raise ValueError("parent_version is required")
        running = self.latest_run()
        if running is not None and running.get("status") == RUNNING:
            raise EvolutionError(
                f"Run {running['run_id']} is still running; resume it instead"
            )

        run_number = self._next_run_number()
        run_id = f"run_{run_number}"
        run = {
            "schema_version": RUN_SCHEMA_VERSION,
            "run_id": run_id,
            "status": RUNNING,
            "parent_version": str(parent_version),
            "adapter": str(adapter or ""),
            "acceptance": acceptance or {},
            "budget": self._resolve_budget(max_rounds),
            "min_rejects_before_incomplete": self._resolve_min_rejects(),
            "round": 0,
            "current_hypothesis": "",
            "current_candidate": "",
            "accepted_version": "",
            "end_reason": "",
            "created_at": _now(),
            "updated_at": _now(),
        }
        self._run_dir_for(run_id).mkdir(parents=True, exist_ok=True)
        self._run = run
        self._save_run()
        return dict(run)

    def resume(self, run_id: Optional[str] = None) -> Dict[str, Any]:
        """Resume a running run, reusing its confirmed budget.

        Resume never re-asks for the budget. Resuming a terminal run raises so
        finished runs are not silently reopened.
        """
        run = self._load_run(run_id) if run_id else self.latest_run()
        if run is None:
            raise EvolutionError("No evolution run found to resume")
        if run.get("status") != RUNNING:
            raise EvolutionError(
                f"Run {run.get('run_id')} already ended with status "
                f"{run.get('status')!r}; start a new run instead"
            )
        self._run = run
        return dict(run)

    def latest_run(self) -> Optional[Dict[str, Any]]:
        """Return the most recent run record, or None when no run exists."""
        evolution_dir = self._evolution_dir()
        if not evolution_dir.is_dir():
            return None
        numbers = []
        for child in evolution_dir.iterdir():
            match = _RUN_DIR_RE.match(child.name)
            if match and child.is_dir():
                numbers.append(int(match.group(1)))
        if not numbers:
            return None
        return self._load_run(f"run_{max(numbers)}")

    def finalize(self) -> Dict[str, Any]:
        """Final guard before reporting the run outcome to the user.

        Raises while the run is still ``running``: a run may only end through
        Accept or a legitimate Incomplete stop.
        """
        run = self._require_run()
        if run["status"] == RUNNING:
            raise EvolutionError(
                "Run is still running; accept a Candidate or mark the run "
                "incomplete before finalizing"
            )
        return dict(run)

    # ---- rounds --------------------------------------------------------------

    def begin_round(self, hypothesis: str, candidate_version: str) -> int:
        """Open the next round for one formal Candidate.

        Enforces the frozen budget: when no round remains, the run becomes
        ``incomplete / budget_exhausted`` and cannot continue without an
        explicit budget extension.
        """
        run = self._require_running()
        if run["round"] >= int(run["budget"]["max_rounds"]):
            self.mark_incomplete("budget_exhausted")
            raise EvolutionBudgetExhausted(
                f"Budget exhausted after {run['round']} rounds; extend the "
                "budget (with user confirmation) or end the run"
            )
        run["round"] += 1
        run["current_hypothesis"] = str(hypothesis or "")
        run["current_candidate"] = str(candidate_version or "")
        self._save_run()
        return int(run["round"])

    def rejected_count(self) -> int:
        """Number of formally rejected candidates in this run so far."""
        path = self.run_dir / "rounds.jsonl"
        if not path.is_file():
            return 0
        rejected = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("decision") == "reject":
                rejected += 1
        return rejected

    def must_continue(self) -> bool:
        """True while the run is still running and needs another Candidate."""
        return self._require_run().get("status") == RUNNING

    def record_round(
        self,
        *,
        decision: str,
        metrics: Optional[Dict[str, Any]] = None,
        artifact_refs: Optional[List[str]] = None,
        notes: str = "",
    ) -> Dict[str, Any]:
        """Append the finished-round summary to ``rounds.jsonl``.

        Only ``reject`` is recorded here; acceptance flows through
        :meth:`accept` so publication and state change stay atomic. Reject
        keeps the run ``running`` for the next round.
        """
        if decision != "reject":
            raise ValueError(
                "record_round only records rejects; use accept() or "
                "mark_incomplete() for the other outcomes"
            )
        run = self._require_running()
        entry = {
            "round": int(run["round"]),
            "hypothesis": run.get("current_hypothesis", ""),
            "candidate": run.get("current_candidate", ""),
            "metrics": metrics or {},
            "decision": decision,
            "artifact_refs": list(artifact_refs or []),
            "notes": str(notes or ""),
            "recorded_at": _now(),
        }
        rounds_path = self.run_dir / "rounds.jsonl"
        with rounds_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._save_run()
        return entry

    def extend_budget(self, max_rounds: int) -> Dict[str, Any]:
        """Raise the frozen round budget after renewed user confirmation."""
        run = self._require_running()
        new_budget = int(max_rounds)
        if new_budget <= int(run["budget"]["max_rounds"]):
            raise ValueError(
                "extend_budget must increase max_rounds "
                f"(current: {run['budget']['max_rounds']})"
            )
        run["budget"]["max_rounds"] = new_budget
        self._save_run()
        return dict(run)

    # ---- evaluations ---------------------------------------------------------

    def record_evaluation(
        self,
        subject: str,
        result: Dict[str, Any],
        *,
        role: str = "",
    ) -> Path:
        """Persist a stable summary of a formal Parent/Candidate evaluation.

        ``result`` is the (normalized) adapter result. Raw artifacts stay at
        their benchmark/user location; only the summary and path references
        are copied into the run.
        """
        self._require_run()
        normalized = normalize_result(result)
        summary = {
            "subject": str(subject),
            "role": str(role or ""),
            "round": int(self._require_run()["round"]),
            "metrics": normalized.get("metrics", {}),
            "cases": normalized.get("cases", []),
            "artifact_paths": normalized.get("artifact_paths", []),
            "provenance": normalized.get("provenance", "unspecified"),
            "gate_input": normalized.get("gate_input"),
            "recorded_at": _now(),
        }
        evaluations_dir = self.run_dir / "evaluations"
        evaluations_dir.mkdir(parents=True, exist_ok=True)
        safe_subject = re.sub(r"[^A-Za-z0-9._-]+", "_", str(subject)).strip("_") or "subject"
        safe_role = re.sub(r"[^A-Za-z0-9._-]+", "_", str(role)).strip("_")
        name = f"round{summary['round']}"
        if safe_role:
            name += f"_{safe_role}"
        path = evaluations_dir / f"{name}_{safe_subject}.json"
        _write_json_atomic(path, summary)
        return path

    # ---- trajectory sources ----------------------------------------------------

    def confirm_trajectory_sources(
        self, sources: List[Dict[str, Any]]
    ) -> Path:
        """Write the user-confirmed trajectory source references.

        Only references are stored; trajectory files are never copied. Each
        entry needs a ``path`` and may carry ``scope`` and ``purpose``; core
        stamps ``confirmed_at``.
        """
        self._require_run()
        normalized: List[Dict[str, Any]] = []
        for source in sources or []:
            if not isinstance(source, dict) or not str(source.get("path", "")).strip():
                raise ValueError("each trajectory source needs a non-empty 'path'")
            normalized.append(
                {
                    "path": str(source["path"]),
                    "scope": str(source.get("scope", "")),
                    "purpose": str(source.get("purpose", "")),
                    "confirmed_at": _now(),
                }
            )
        path = self.run_dir / "trajectory-sources.json"
        _write_json_atomic(path, {"sources": normalized})
        return path

    def trajectory_sources(self) -> List[Dict[str, Any]]:
        """Return the confirmed sources of the current run."""
        path = self.run_dir / "trajectory-sources.json"
        if not path.is_file():
            return []
        data = _read_json(path)
        sources = data.get("sources")
        return list(sources) if isinstance(sources, list) else []

    def previous_trajectory_sources(self) -> List[Dict[str, Any]]:
        """Return the newest source record from earlier runs (for reuse).

        A new run defaults to these references after verifying the paths are
        still valid; re-confirmation is only needed when sources change.
        """
        evolution_dir = self._evolution_dir()
        if not evolution_dir.is_dir():
            return []
        numbers = []
        for child in evolution_dir.iterdir():
            match = _RUN_DIR_RE.match(child.name)
            if match and child.is_dir():
                numbers.append(int(match.group(1)))
        current = self._run["run_id"] if self._run else None
        for number in sorted(numbers, reverse=True):
            run_id = f"run_{number}"
            if run_id == current:
                continue
            path = evolution_dir / run_id / "trajectory-sources.json"
            if path.is_file():
                data = _read_json(path)
                sources = data.get("sources")
                if isinstance(sources, list):
                    return list(sources)
        return []

    # ---- decision --------------------------------------------------------------

    def accept(self, new_version: Optional[str] = None) -> str:
        """Accept the current Candidate: validate, publish, activate, advance.

        The Candidate is published as a new official version without
        overwriting existing ones, ``active.json`` is switched, and the
        evolution checkpoint advances. Only this path ends a run in success.
        """
        run = self._require_running()
        candidate = str(run.get("current_candidate") or "")
        if not candidate:
            raise EvolutionError("No Candidate under evaluation to accept")
        validation = validate(str(self.workspace), version=candidate)
        if not validation["passed"]:
            raise EvolutionError(f"Candidate validation failed: {validation['errors']}")
        gate = self._publication_gate(run)
        if not gate["accept"]:
            raise EvolutionError("Candidate did not pass the recorded evaluation gate")
        # Validate the Candidate loads before anything else changes.
        SemanticStore.load_version(self.workspace, candidate)
        target = str(new_version or "").strip() or self._next_official_version()
        SemanticStore.publish(self.workspace, candidate, target)
        EvolutionTrigger(str(self.workspace)).advance_checkpoint()
        run["status"] = ACCEPTED
        run["accepted_version"] = target
        run["end_reason"] = ""
        run["gate"] = gate
        self._save_run()
        return target

    def _publication_gate(self, run):
        summaries = []
        for path in (self.run_dir / "evaluations").glob("*.json"):
            summary = _read_json(path)
            if summary.get("round") == run["round"] and summary.get("subject") == run["current_candidate"]:
                summaries.append(summary)
        summaries.sort(key=lambda s: s.get("recorded_at", ""), reverse=True)
        supplied = next((s.get("gate_input") for s in summaries if s.get("gate_input")), None)
        if not isinstance(supplied, dict):
            raise EvolutionError("Record candidate evaluation gate_input before publication")
        if supplied.get("unacceptable_regressions") is not False:
            raise EvolutionError("Evaluation must explicitly rule out unacceptable regressions")
        protocol = supplied.get("protocol")
        expected = run.get("acceptance", {}).get("protocol")
        if expected and protocol != expected:
            raise EvolutionError("Gate protocol differs from the frozen acceptance protocol")
        if protocol == "ground_truth":
            parent = supplied.get("parent_scores", [])
            candidate = supplied.get("candidate_scores", [])
            cases = supplied.get("case_ids", [])
            if not parent or len(parent) != len(candidate) or len(cases) != len(parent) or len(set(cases)) != len(cases):
                raise EvolutionError("Gate needs paired scores with unique matching case_ids")
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in parent + candidate):
                raise EvolutionError("Gate scores must be finite numbers")
            return EvaluationGate.decide_gt(parent, candidate)
        if protocol == "llm_judge":
            verdicts = supplied.get("verdicts", [])
            if not verdicts or any(v.get("winner") not in {"parent", "candidate", "tie"}
                                   or not isinstance(v.get("critical_error"), bool) for v in verdicts):
                raise EvolutionError("Gate needs nonempty valid judge verdicts")
            return EvaluationGate.decide_judge(verdicts)
        raise EvolutionError("Unknown evaluation gate protocol")

    def mark_incomplete(self, reason: str) -> Dict[str, Any]:
        """Stop the run for a legitimate external reason.

        Reject and ordinary stagnation are not valid reasons; only external
        conditions such as budget exhaustion, user interruption, missing
        data/permissions, or unreliable evaluation qualify. Neither the active
        version nor the checkpoint changes.
        """
        run = self._require_running()
        normalized_reason = str(reason or "").strip()
        if normalized_reason not in INCOMPLETE_REASONS:
            raise ValueError(
                f"incomplete reason must be one of {sorted(INCOMPLETE_REASONS)}"
            )
        if normalized_reason in {"missing_data", "unreliable_evaluation", "external_block"}:
            required = int(
                run.get("min_rejects_before_incomplete", DEFAULT_MIN_REJECTS_BEFORE_INCOMPLETE)
            )
            if self.rejected_count() < required:
                raise EvolutionError(
                    f"Cannot stop for {normalized_reason!r}: the run is still running "
                    f"and has {self.rejected_count()} rejected candidate(s); at least "
                    f"{required} rejected candidates are required before this external "
                    "stop is allowed. Design and evaluate the next Candidate in this "
                    "run instead."
                )
        if normalized_reason == "budget_exhausted" and run["round"] < int(
            run["budget"]["max_rounds"]
        ):
            raise EvolutionError(
                "Cannot stop for budget_exhausted: the round budget has not been spent "
                "yet. Continue the loop; begin_round raises EvolutionBudgetExhausted "
                "automatically when the budget is spent."
            )
        run["status"] = INCOMPLETE
        run["end_reason"] = normalized_reason
        self._save_run()
        return dict(run)

    # ---- accessors ---------------------------------------------------------------

    @property
    def run(self) -> Dict[str, Any]:
        return dict(self._require_run())

    @property
    def run_id(self) -> str:
        return str(self._require_run()["run_id"])

    @property
    def status(self) -> str:
        return str(self._require_run()["status"])

    @property
    def run_dir(self) -> Path:
        run = self._require_run()
        return self._run_dir_for(str(run["run_id"]))

    # ---- internals -------------------------------------------------------------

    def _evolution_dir(self) -> Path:
        return self.workspace / "evolution"

    def _run_dir_for(self, run_id: str) -> Path:
        return self._evolution_dir() / run_id

    def _next_run_number(self) -> int:
        latest = self.latest_run()
        if latest is None:
            return 1
        match = _RUN_DIR_RE.match(str(latest.get("run_id", "")))
        return int(match.group(1)) + 1 if match else 1

    def _load_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        path = self._run_dir_for(run_id) / "run.json"
        if not path.is_file():
            return None
        run = _read_json(path)
        if not isinstance(run, dict) or run.get("run_id") != run_id:
            raise EvolutionError(f"Corrupt run record: {path}")
        return run

    def _require_run(self) -> Dict[str, Any]:
        if self._run is None:
            run = self.latest_run()
            if run is None:
                raise EvolutionError("No evolution run loaded; start or resume one")
            self._run = run
        return self._run

    def _require_running(self) -> Dict[str, Any]:
        run = self._require_run()
        if run.get("status") != RUNNING:
            raise EvolutionError(
                f"Run {run.get('run_id')} is {run.get('status')!r}; only a "
                "running run can continue"
            )
        return run

    def _save_run(self) -> None:
        run = self._require_run()
        run["updated_at"] = _now()
        ensure_workspace(self.workspace)
        _write_json_atomic(self.run_dir / "run.json", run)

    def _resolve_budget(self, max_rounds: Optional[int]) -> Dict[str, int]:
        if max_rounds is not None:
            value = int(max_rounds)
        else:
            value = 0
            try:
                project = load_project(self.workspace)
                settings = project.get("evolution")
                if isinstance(settings, dict) and settings.get("max_rounds"):
                    value = int(settings["max_rounds"])
            except (FileNotFoundError, ValueError, TypeError):
                value = 0
            if value <= 0:
                value = DEFAULT_MAX_ROUNDS
        if value <= 0:
            raise ValueError("max_rounds must be a positive integer")
        return {"max_rounds": value}

    def _resolve_min_rejects(self) -> int:
        """Resolve the minimum rejected rounds before a judgment-based stop."""
        value = 0
        try:
            project = load_project(self.workspace)
            settings = project.get("evolution")
            if isinstance(settings, dict) and settings.get(
                "min_rejects_before_incomplete"
            ) is not None:
                value = int(settings["min_rejects_before_incomplete"])
        except (FileNotFoundError, ValueError, TypeError):
            value = 0
        if value <= 0:
            value = DEFAULT_MIN_REJECTS_BEFORE_INCOMPLETE
        return value

    def _next_official_version(self) -> str:
        highest = 0
        for name in SemanticStore.list_versions(self.workspace):
            match = _OFFICIAL_VERSION_RE.match(name)
            if match:
                highest = max(highest, int(match.group(1)))
        return f"ontology_v{highest + 1}"
