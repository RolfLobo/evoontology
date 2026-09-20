"""EvolutionSession lifecycle tests: state machine, budget, publish safety."""

import json

import pytest

from evoontology import (
    EvolutionBudgetExhausted,
    EvolutionError,
    EvolutionSession,
    SemanticStore,
    ensure_workspace,
    normalize_result,
)

SAMPLE = {
    "terms": [{"id": "t1", "name": "net_income", "type": "metric", "definition": "net income"}],
    "mappings": [{"id": "m1", "term_id": "t1", "table": "financials", "column": "net_income"}],
    "relations": [],
    "constraints": [],
    "evidence": [],
}


def _candidate(extra_id="t2"):
    records = {k: list(v) for k, v in SAMPLE.items()}
    records["terms"] = SAMPLE["terms"] + [{"id": extra_id, "name": f"term_{extra_id}", "type": "metric"}]
    return records


def _setup(tmp_path):
    ensure_workspace(str(tmp_path))
    SemanticStore.save_version(str(tmp_path), "ontology_v0", SAMPLE)
    SemanticStore.set_active(str(tmp_path), "ontology_v0")
    return tmp_path


def test_start_run_records_frozen_budget(tmp_path):
    ws = _setup(tmp_path)
    session = EvolutionSession(str(ws))
    run = session.start_run("ontology_v0", adapter="bird", max_rounds=3)
    assert run["status"] == "running"
    assert run["budget"] == {"max_rounds": 3}
    assert run["parent_version"] == "ontology_v0"
    assert (ws / "evolution" / "run_1" / "run.json").is_file()
    # a second run is blocked while one is still running
    with pytest.raises(EvolutionError):
        EvolutionSession(str(ws)).start_run("ontology_v0")


def test_budget_defaults_to_eight_rounds(tmp_path):
    ws = _setup(tmp_path)
    session = EvolutionSession(str(ws))
    assert session.start_run("ontology_v0")["budget"] == {"max_rounds": 8}


def test_budget_priority_explicit_over_project_setting(tmp_path):
    ws = _setup(tmp_path)
    project = {
        "schema_version": 1,
        "mode": "fixed_split",
        "data_source": "BIRD minidev",
        "workload_source": "trajectories",
        "evaluation": {"benchmark": "bird"},
        "boundary": {"scope": "33 tasks"},
        "evolution": {"max_rounds": 5},
    }
    (ws / "project.json").write_text(json.dumps(project), encoding="utf-8")
    session = EvolutionSession(str(ws))
    assert session.start_run("ontology_v0")["budget"] == {"max_rounds": 5}
    session.mark_incomplete("user_interrupted")
    assert session.start_run("ontology_v0", max_rounds=2)["budget"] == {"max_rounds": 2}


def test_reject_keeps_run_running(tmp_path):
    ws = _setup(tmp_path)
    session = EvolutionSession(str(ws))
    session.start_run("ontology_v0", max_rounds=2)
    assert session.begin_round("hypothesis", "v0-c1") == 1
    SemanticStore.save_version(str(ws), "v0-c1", _candidate())
    session.record_evaluation("v0-c1", {"metrics": {"ex": 0.5}}, role="candidate")
    entry = session.record_round(decision="reject", metrics={"ex": 0.5})
    assert entry["decision"] == "reject"
    assert session.status == "running"
    assert SemanticStore.active_version(str(ws)) == "ontology_v0"
    lines = (session.run_dir / "rounds.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["candidate"] == "v0-c1"


def test_record_round_only_accepts_reject(tmp_path):
    ws = _setup(tmp_path)
    session = EvolutionSession(str(ws))
    session.start_run("ontology_v0")
    session.begin_round("h", "v0-c1")
    with pytest.raises(ValueError):
        session.record_round(decision="accept")


def test_candidate_evaluation_does_not_touch_active(tmp_path):
    ws = _setup(tmp_path)
    session = EvolutionSession(str(ws))
    session.start_run("ontology_v0")
    session.begin_round("h", "v0-c1")
    SemanticStore.save_version(str(ws), "v0-c1", _candidate())
    session.record_evaluation("v0-c1", {"metrics": {"ex": 0.6}}, role="candidate")
    assert SemanticStore.active_version(str(ws)) == "ontology_v0"
    assert not (ws / "state.json").exists()


def _record_passing_gate(session):
    session.record_evaluation(session.run["current_candidate"], {"metrics": {}, "gate_input": {
        "protocol": "ground_truth", "case_ids": ["independent_case"],
        "parent_scores": [0], "candidate_scores": [1], "unacceptable_regressions": False,
    }}, role="candidate")


def test_publication_refuses_missing_or_failed_gate(tmp_path):
    ws = _setup(tmp_path)
    session = EvolutionSession(str(ws))
    session.start_run("ontology_v0")
    session.begin_round("h", "candidate")
    SemanticStore.save_version(str(ws), "candidate", _candidate())
    with pytest.raises(EvolutionError, match="gate_input"):
        session.accept()
    session.record_evaluation("candidate", {"metrics": {}, "gate_input": {
        "protocol": "ground_truth", "case_ids": ["q"], "parent_scores": [1],
        "candidate_scores": [0], "unacceptable_regressions": False}}, role="candidate")
    with pytest.raises(EvolutionError, match="did not pass"):
        session.accept()
    assert SemanticStore.active_version(str(ws)) == "ontology_v0"
    assert session.status == "running"


def test_accept_publishes_and_advances_checkpoint(tmp_path):
    ws = _setup(tmp_path)
    session = EvolutionSession(str(ws))
    session.start_run("ontology_v0")
    session.begin_round("h", "v0-c1")
    SemanticStore.save_version(str(ws), "v0-c1", _candidate())
    _record_passing_gate(session)
    assert session.accept() == "ontology_v1"
    assert session.status == "accepted"
    assert SemanticStore.active_version(str(ws)) == "ontology_v1"
    state = json.loads((ws / "state.json").read_text(encoding="utf-8"))
    assert state["checkpoint_time"]
    final = session.finalize()
    assert final["status"] == "accepted"
    assert final["accepted_version"] == "ontology_v1"


def test_accept_counts_legacy_versions_but_publishes_canonical_name(tmp_path):
    ensure_workspace(str(tmp_path))
    SemanticStore.save_version(str(tmp_path), "semantic_v3", SAMPLE)
    SemanticStore.set_active(str(tmp_path), "semantic_v3")
    session = EvolutionSession(str(tmp_path))
    session.start_run("semantic_v3")
    session.begin_round("h", "v3-c1")
    SemanticStore.save_version(str(tmp_path), "v3-c1", _candidate())

    _record_passing_gate(session)
    assert session.accept() == "ontology_v4"
    assert SemanticStore.active_version(str(tmp_path)) == "ontology_v4"


def test_accept_requires_candidate(tmp_path):
    ws = _setup(tmp_path)
    session = EvolutionSession(str(ws))
    session.start_run("ontology_v0")
    with pytest.raises(EvolutionError):
        session.accept()


def test_finalize_requires_terminal_state(tmp_path):
    ws = _setup(tmp_path)
    session = EvolutionSession(str(ws))
    session.start_run("ontology_v0")
    with pytest.raises(EvolutionError):
        session.finalize()


def test_budget_exhaustion_marks_incomplete(tmp_path):
    ws = _setup(tmp_path)
    session = EvolutionSession(str(ws))
    session.start_run("ontology_v0", max_rounds=2)
    for number in (1, 2):
        assert session.begin_round("h", f"v0-c{number}") == number
        session.record_round(decision="reject")
    with pytest.raises(EvolutionBudgetExhausted):
        session.begin_round("h", "v0-c3")
    assert session.status == "incomplete"
    assert session.finalize()["end_reason"] == "budget_exhausted"
    assert SemanticStore.active_version(str(ws)) == "ontology_v0"


def test_extend_budget_requires_increase_and_running_run(tmp_path):
    ws = _setup(tmp_path)
    session = EvolutionSession(str(ws))
    session.start_run("ontology_v0", max_rounds=2)
    with pytest.raises(ValueError):
        session.extend_budget(2)
    session.extend_budget(3)
    for number in (1, 2, 3):
        assert session.begin_round("h", f"v0-c{number}") == number
        session.record_round(decision="reject")
    session.mark_incomplete("user_interrupted")
    with pytest.raises(EvolutionError):
        session.extend_budget(4)


def test_resume_reuses_frozen_budget(tmp_path):
    ws = _setup(tmp_path)
    session = EvolutionSession(str(ws))
    session.start_run("ontology_v0", max_rounds=3)
    session.begin_round("h", "v0-c1")
    session.record_round(decision="reject")

    resumed = EvolutionSession(str(ws)).resume()
    assert resumed["run_id"] == "run_1"
    assert resumed["budget"] == {"max_rounds": 3}
    assert resumed["round"] == 1
    resumed_by_id = EvolutionSession(str(ws)).resume("run_1")
    assert resumed_by_id["budget"] == {"max_rounds": 3}


def test_resume_rejects_terminal_runs(tmp_path):
    ws = _setup(tmp_path)
    session = EvolutionSession(str(ws))
    session.start_run("ontology_v0")
    session.begin_round("h", "v0-c1")
    SemanticStore.save_version(str(ws), "v0-c1", _candidate())
    _record_passing_gate(session)
    session.accept()
    with pytest.raises(EvolutionError):
        EvolutionSession(str(ws)).resume("run_1")
    with pytest.raises(EvolutionError):
        EvolutionSession(str(ws)).resume()


def test_resume_missing_run_raises(tmp_path):
    ws = _setup(tmp_path)
    with pytest.raises(EvolutionError):
        EvolutionSession(str(ws)).resume()


def test_mark_incomplete_validates_reason(tmp_path):
    ws = _setup(tmp_path)
    session = EvolutionSession(str(ws))
    session.start_run("ontology_v0")
    with pytest.raises(ValueError):
        session.mark_incomplete("poor_metrics")
    # Immediate external reasons do not require rejected candidates.
    session.mark_incomplete("user_interrupted")
    assert session.status == "incomplete"
    assert session.finalize()["end_reason"] == "user_interrupted"
    assert SemanticStore.active_version(str(ws)) == "ontology_v0"
    assert not (ws / "state.json").exists()


def test_mark_incomplete_judgment_reasons_require_rejected_rounds(tmp_path):
    ws = _setup(tmp_path)
    session = EvolutionSession(str(ws))
    session.start_run("ontology_v0", max_rounds=4)
    for reason in ("missing_data", "unreliable_evaluation", "external_block"):
        with pytest.raises(EvolutionError):
            session.mark_incomplete(reason)
    session.begin_round("h1", "v0-c1")
    session.record_round(decision="reject")
    with pytest.raises(EvolutionError):
        session.mark_incomplete("missing_data")
    session.begin_round("h2", "v0-c2")
    session.record_round(decision="reject")
    session.mark_incomplete("missing_data")
    assert session.status == "incomplete"
    assert session.finalize()["end_reason"] == "missing_data"


def test_min_rejects_before_incomplete_configurable(tmp_path):
    ws = _setup(tmp_path)
    project = {
        "schema_version": 1,
        "mode": "fixed_split",
        "data_source": "x",
        "workload_source": "y",
        "evaluation": {"benchmark": "bird"},
        "boundary": {"scope": "n"},
        "evolution": {"min_rejects_before_incomplete": 1},
    }
    (ws / "project.json").write_text(json.dumps(project), encoding="utf-8")
    session = EvolutionSession(str(ws))
    run = session.start_run("ontology_v0", max_rounds=4)
    assert run["min_rejects_before_incomplete"] == 1
    with pytest.raises(EvolutionError):
        session.mark_incomplete("missing_data")
    session.begin_round("h1", "v0-c1")
    session.record_round(decision="reject")
    session.mark_incomplete("missing_data")
    assert session.status == "incomplete"


def test_mark_incomplete_budget_exhausted_requires_spent_budget(tmp_path):
    ws = _setup(tmp_path)
    session = EvolutionSession(str(ws))
    session.start_run("ontology_v0", max_rounds=2)
    with pytest.raises(EvolutionError):
        session.mark_incomplete("budget_exhausted")


def test_rejected_count_and_must_continue(tmp_path):
    ws = _setup(tmp_path)
    session = EvolutionSession(str(ws))
    session.start_run("ontology_v0", max_rounds=4)
    assert session.must_continue() is True
    assert session.rejected_count() == 0
    session.begin_round("h1", "v0-c1")
    session.record_round(decision="reject")
    assert session.rejected_count() == 1
    assert session.must_continue() is True


def test_trajectory_sources_persist_and_reuse(tmp_path):
    ws = _setup(tmp_path)
    session = EvolutionSession(str(ws))
    session.start_run("ontology_v0")
    with pytest.raises(ValueError):
        session.confirm_trajectory_sources([{"scope": "no path"}])
    session.confirm_trajectory_sources([
        {"path": "results/bird/minidev", "scope": "33 tasks", "purpose": "diagnosis"},
    ])
    sources = session.trajectory_sources()
    assert len(sources) == 1
    assert sources[0]["path"] == "results/bird/minidev"
    assert sources[0]["confirmed_at"]
    session.mark_incomplete("user_interrupted")

    next_session = EvolutionSession(str(ws))
    assert next_session.previous_trajectory_sources()[0]["path"] == "results/bird/minidev"
    next_session.start_run("ontology_v0")
    assert next_session.trajectory_sources() == []


def test_publish_never_overwrites(tmp_path):
    ws = _setup(tmp_path)
    SemanticStore.save_version(str(ws), "v0-c1", _candidate())
    assert SemanticStore.publish(str(ws), "v0-c1", "ontology_v1") == "ontology_v1"
    # identical content is a safe retry
    assert SemanticStore.publish(str(ws), "v0-c1", "ontology_v1") == "ontology_v1"
    # different content must not replace the published version
    SemanticStore.save_version(str(ws), "v0-c2", _candidate("t3"))
    with pytest.raises(FileExistsError):
        SemanticStore.publish(str(ws), "v0-c2", "ontology_v1")


def test_record_evaluation_normalizes_and_rejects_bad_result(tmp_path):
    ws = _setup(tmp_path)
    session = EvolutionSession(str(ws))
    session.start_run("ontology_v0")
    session.begin_round("h", "v0-c1")
    path = session.record_evaluation(
        "v0-c1",
        {"metrics": {"ex": 0.7}, "cases": [{"id": 1, "score": 1.0, "status": "correct"}]},
        role="candidate",
    )
    summary = json.loads(path.read_text(encoding="utf-8"))
    assert summary["subject"] == "v0-c1"
    assert summary["role"] == "candidate"
    assert summary["artifact_paths"] == []
    with pytest.raises(ValueError):
        session.record_evaluation("v0-c1", {"cases": []})


def test_normalize_result_contract():
    normalized = normalize_result({"metrics": {"ex": 0.5}})
    assert normalized["cases"] == []
    assert normalized["artifact_paths"] == []
    with pytest.raises(ValueError):
        normalize_result({"metrics": "bad"})
    with pytest.raises(ValueError):
        normalize_result("not a dict")
