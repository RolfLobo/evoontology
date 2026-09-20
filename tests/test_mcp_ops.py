"""Tests for the deterministic build/evolve/visualize MCP operations."""


from evoontology import SemanticStore
from evoontology.runtime import ops
from evoontology.visualization import VISUALIZATION_FILENAME

SAMPLE = {
    "terms": [{"id": "t1", "name": "revenue", "type": "metric", "definition": "Revenue"}],
    "mappings": [{"id": "m1", "term_id": "t1", "table": "financials", "column": "revenue"}],
    "relations": [],
    "constraints": [],
    "evidence": [{"id": "e1", "source": "schema", "query": "PRAGMA table_info(financials)"}],
}


def _ws(tmp_path):
    return str(tmp_path / ".evoontology")


def _save_active(ws, version="ontology_v0", records=SAMPLE):
    SemanticStore.save_version(ws, version, records)
    SemanticStore.set_active(ws, version)


def test_build_publish_flow(tmp_path):
    ws = _ws(tmp_path)
    assert ops.execute("save_version", {"workspace": ws, "version": "ontology_v0", "records": SAMPLE})["status"] == "ok"
    assert ops.execute("validate_semantics", {"workspace": ws, "version": "ontology_v0"})["passed"] is True
    assert ops.execute("set_active_version", {"workspace": ws, "version": "ontology_v0"})["active_version"] == "ontology_v0"
    status = ops.execute("evolution_status", {"workspace": ws})
    assert status["check"]["evolution_due"] is False
    assert (tmp_path / ".evoontology" / "state.json").is_file()


def test_validate_and_list_versions(tmp_path):
    ws = _ws(tmp_path)
    _save_active(ws)
    assert ops.execute("validate_semantics", {"workspace": ws})["passed"] is True
    listing = ops.execute("list_versions", {"workspace": ws})
    assert listing["active_version"] == "ontology_v0"
    assert listing["versions"] == ["ontology_v0"]


def test_visualize_ontology_writes_html(tmp_path):
    ws = _ws(tmp_path)
    _save_active(ws)
    result = ops.execute("visualize_ontology", {"workspace": ws, "open_browser": False})
    assert result["status"] == "ok"
    assert result["opened_in_browser"] is False
    assert (tmp_path / ".evoontology" / "visualizations" / VISUALIZATION_FILENAME).is_file()


def test_visualize_semantics_remains_a_compatibility_alias(tmp_path):
    ws = _ws(tmp_path)
    _save_active(ws)

    result = ops.execute("visualize_semantics", {"workspace": ws, "open_browser": False})

    assert result["status"] == "ok"
    assert result["html_path"].endswith(VISUALIZATION_FILENAME)


def test_visualize_ontology_reports_discovered_nested_workspace(tmp_path):
    container = tmp_path / ".evoontology"
    nested = container / "database_a" / "workspace_a"
    _save_active(str(nested))

    result = ops.execute(
        "visualize_ontology", {"workspace": str(container), "open_browser": False}
    )

    assert result["workspace"] == str(nested.resolve())
    assert result["html_path"] == str(
        nested.resolve() / "visualizations" / VISUALIZATION_FILENAME
    )


def test_visualize_ontology_opens_browser_by_default(tmp_path, monkeypatch):
    import evoontology.visualization.renderer as renderer

    opened = []
    monkeypatch.setattr(renderer.webbrowser, "open", lambda url: opened.append(url) or True)
    ws = _ws(tmp_path)
    _save_active(ws)
    result = ops.execute("visualize_ontology", {"workspace": ws})
    assert result["opened_in_browser"] is True
    assert len(opened) == 1
    assert opened[0].endswith(VISUALIZATION_FILENAME)


def test_evolution_accept_flow(tmp_path):
    ws = _ws(tmp_path)
    _save_active(ws)
    run = ops.execute("start_evolution_run", {"workspace": ws, "parent_version": "ontology_v0", "max_rounds": 2})
    assert run["status"] == "running"
    assert ops.execute("begin_evolution_round", {"workspace": ws, "hypothesis": "h", "candidate_version": "v0-c1"})["round"] == 1

    candidate = {k: list(v) for k, v in SAMPLE.items()}
    candidate["terms"] = SAMPLE["terms"] + [{"id": "t2", "name": "profit", "type": "metric"}]
    ops.execute("save_version", {"workspace": ws, "version": "v0-c1", "records": candidate})
    ops.execute("record_evolution_evaluation", {"workspace": ws, "subject": "v0-c1", "result": {"metrics": {"ex": 0.6}}, "role": "candidate"})

    ops.execute("record_evolution_evaluation", {"workspace": ws, "subject": "v0-c1", "role": "candidate", "result": {"metrics": {"ex": 0.6}, "gate_input": {
        "protocol": "ground_truth", "case_ids": ["case1"], "parent_scores": [0.4], "candidate_scores": [0.6], "unacceptable_regressions": False}}})
    accepted = ops.execute("accept_evolution", {"workspace": ws})
    assert accepted["accepted_version"] == "ontology_v1"
    assert SemanticStore.active_version(ws) == "ontology_v1"
    assert ops.execute("finalize_evolution_run", {"workspace": ws, "open_browser": False})["status"] == "accepted"


def test_record_reject_keeps_run_running(tmp_path):
    ws = _ws(tmp_path)
    _save_active(ws)
    ops.execute("start_evolution_run", {"workspace": ws, "parent_version": "ontology_v0"})
    ops.execute("begin_evolution_round", {"workspace": ws, "hypothesis": "h", "candidate_version": "v0-c1"})
    entry = ops.execute("record_evolution_round", {"workspace": ws, "decision": "reject", "metrics": {"ex": 0.4}})
    assert entry["decision"] == "reject"
    assert ops.execute("evolution_run_status", {"workspace": ws})["run"]["status"] == "running"
    assert SemanticStore.active_version(ws) == "ontology_v0"


def test_mark_incomplete_does_not_publish(tmp_path):
    ws = _ws(tmp_path)
    _save_active(ws)
    ops.execute("start_evolution_run", {"workspace": ws, "parent_version": "ontology_v0"})
    ops.execute("mark_evolution_incomplete", {"workspace": ws, "reason": "user_interrupted"})
    assert ops.execute("evolution_run_status", {"workspace": ws})["run"]["status"] == "incomplete"
    assert SemanticStore.active_version(ws) == "ontology_v0"
    assert not (tmp_path / ".evoontology" / "state.json").exists()
