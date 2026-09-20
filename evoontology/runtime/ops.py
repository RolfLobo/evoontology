"""Deterministic build/evolve/visualize operations served by the MCP server.

These wrap the core's validate, visualize, trigger, store, and evolution-session
capabilities. They exist so a plugin-only installation (no repo clone, no
``pip install evoontology``) can still drive the full build and evolve loop:
the MCP server boots from the plugin root where the bundled core lives, and the
agent calls these tools with an explicit workspace path.
"""

from __future__ import annotations

import webbrowser
from typing import Any, Dict

from ..evolution.session import EvolutionSession
from ..ontology.store import SemanticStore
from ..trigger.trigger import EvolutionTrigger
from ..validate import validate
from ..visualization import visualize as _visualize
from ..visualization.preview import ensure_preview
from ..workflow import ProjectWorkflow, read_json, write_json
from ..workspace import resolve_workspace


def _workspace(arguments: Dict[str, Any]):
    raw = str(arguments.get("workspace") or "").strip()
    if not raw:
        raise ValueError(
            "workspace is required: pass the absolute path to the .evoontology/ directory"
        )
    return resolve_workspace(raw)


def _version(arguments: Dict[str, Any]) -> str | None:
    raw = str(arguments.get("version") or "").strip()
    return raw or None


def validate_semantics(arguments: Dict[str, Any]) -> Dict[str, Any]:
    return validate(str(_workspace(arguments)), version=_version(arguments))


def visualize_ontology(arguments: Dict[str, Any]) -> Dict[str, Any]:
    workspace = _workspace(arguments)
    presentation = arguments.get("presentation", "external")
    if presentation not in {"codex", "external"}:
        raise ValueError("presentation must be codex or external")
    open_browser = bool(arguments.get("open_browser", True))
    path = _visualize(
        workspace=str(workspace),
        version=_version(arguments) or "active",
        open_browser=False,
    )
    opened = False
    warning = ""
    browser_url = ""
    if presentation == "codex":
        browser_url = ensure_preview(path)
    elif open_browser:
        try:
            opened = bool(webbrowser.open(path.resolve().as_uri()))
        except Exception as exc:
            warning = str(exc)
        if not opened:
            warning = warning or "Browser did not open; use html_path to view the generated result"
    return {
        "status": "ok",
        "workspace": str(path.parent.parent),
        "html_path": str(path),
        "opened_in_browser": opened,
        "warning": warning,
        "presentation": presentation,
        "browser_url": browser_url,
        "next_action": "Open browser_url with the Codex open_in_codex browser tool; reuse an existing tab when available" if browser_url else "",
    }


def evolution_status(arguments: Dict[str, Any]) -> Dict[str, Any]:
    trigger = EvolutionTrigger(str(_workspace(arguments)))
    state = trigger.initialize()
    return {"status": "ok", "state": state, "check": trigger.check()}


def list_versions(arguments: Dict[str, Any]) -> Dict[str, Any]:
    workspace = _workspace(arguments)
    active_version: str | None = None
    try:
        active_version = SemanticStore.active_version(str(workspace))
    except (FileNotFoundError, ValueError):
        active_version = None
    return {
        "status": "ok",
        "active_version": active_version,
        "versions": SemanticStore.list_versions(str(workspace)),
    }


def save_version(arguments: Dict[str, Any]) -> Dict[str, Any]:
    version = str(arguments.get("version") or "").strip()
    records = arguments.get("records")
    if not version:
        raise ValueError("version is required")
    if not isinstance(records, dict):
        raise ValueError("records must be an object with the five record families")
    path = SemanticStore.save_version(str(_workspace(arguments)), version, records)
    return {"status": "ok", "version": version, "path": path}


def set_active_version(arguments: Dict[str, Any]) -> Dict[str, Any]:
    version = str(arguments.get("version") or "").strip()
    if not version:
        raise ValueError("version is required")
    SemanticStore.set_active(str(_workspace(arguments)), version)
    return {"status": "ok", "active_version": version}


def start_evolution_run(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    return session.start_run(
        str(arguments.get("parent_version") or "").strip(),
        adapter=str(arguments.get("adapter") or ""),
        max_rounds=arguments.get("max_rounds") or (2 if arguments.get("profile") == "quick" else None),
        acceptance=arguments.get("acceptance"),
    )


def resume_evolution_run(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    run_id = str(arguments.get("run_id") or "").strip() or None
    return session.resume(run_id)


def evolution_run_status(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    run = session.latest_run()
    return {"status": "ok", "run": run}


def begin_evolution_round(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    round_number = session.begin_round(
        str(arguments.get("hypothesis") or ""),
        str(arguments.get("candidate_version") or ""),
    )
    return {"status": "ok", "round": round_number}


def record_evolution_round(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    return session.record_round(
        decision=str(arguments.get("decision") or ""),
        metrics=arguments.get("metrics"),
        artifact_refs=arguments.get("artifact_refs"),
        notes=str(arguments.get("notes") or ""),
    )


def record_evolution_evaluation(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    path = session.record_evaluation(
        str(arguments.get("subject") or ""),
        arguments.get("result") or {},
        role=str(arguments.get("role") or ""),
    )
    return {"status": "ok", "path": str(path)}


def confirm_trajectory_sources(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    sources = arguments.get("sources")
    if not isinstance(sources, list):
        raise ValueError("sources must be a list of {path, scope, purpose} objects")
    path = session.confirm_trajectory_sources(sources)
    return {"status": "ok", "path": str(path)}


def accept_evolution(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    new_version = str(arguments.get("new_version") or "").strip() or None
    candidate = session.latest_run().get("current_candidate", "")
    published = session.accept(new_version)
    report = read_json(_workspace(arguments) / "reports" / (candidate + ".json"))
    if report:
        report["version"] = published
        write_json(_workspace(arguments) / "reports" / (published + ".json"), report)
    return {"status": "ok", "accepted_version": published}


def mark_evolution_incomplete(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    return session.mark_incomplete(str(arguments.get("reason") or ""))


def extend_evolution_budget(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    max_rounds = arguments.get("max_rounds")
    if max_rounds is None:
        raise ValueError("max_rounds is required")
    return session.extend_budget(int(max_rounds))


def finalize_evolution_run(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    run = session.finalize()
    run["presentation"] = _present(arguments, run.get("accepted_version") or run["parent_version"])
    return run


def _present(arguments, version):
    try:
        return visualize_ontology({**arguments, "version": version})
    except Exception as exc:
        # Delivery failure must never undo a successful publication.
        return {"status": "presentation_failed", "message": str(exc),
                "recovery": "Retry visualize_ontology; the active version is unchanged"}


def publish_ontology_build(arguments):
    workspace = _workspace(arguments)
    if (workspace / "active.json").exists():
        raise ValueError("An active ontology already exists; evolve it instead")
    version = str(arguments.get("version") or "ontology_v0")
    result = validate_semantics({"workspace": str(workspace), "version": version})
    if not result.get("passed"):
        raise ValueError(f"Ontology validation failed: {result}")
    SemanticStore.set_active(workspace, version)
    evolution_status(arguments)
    return {"status": "published", "active_version": version,
            "presentation": _present(arguments, version)}


def workflow_operation(name, arguments):
    workflow = ProjectWorkflow(_workspace(arguments))
    args = {k: v for k, v in arguments.items() if k != "workspace"}
    return getattr(workflow, name)(**args)


_HANDLERS = {
    "publish_ontology_build": publish_ontology_build,
    "validate_semantics": validate_semantics,
    "visualize_ontology": visualize_ontology,
    # Compatibility for clients configured before the ontology terminology update.
    "visualize_semantics": visualize_ontology,
    "evolution_status": evolution_status,
    "list_versions": list_versions,
    "save_version": save_version,
    "set_active_version": set_active_version,
    "start_evolution_run": start_evolution_run,
    "resume_evolution_run": resume_evolution_run,
    "evolution_run_status": evolution_run_status,
    "begin_evolution_round": begin_evolution_round,
    "record_evolution_round": record_evolution_round,
    "record_evolution_evaluation": record_evolution_evaluation,
    "confirm_trajectory_sources": confirm_trajectory_sources,
    "accept_evolution": accept_evolution,
    "mark_evolution_incomplete": mark_evolution_incomplete,
    "extend_evolution_budget": extend_evolution_budget,
    "finalize_evolution_run": finalize_evolution_run,
}

for _tool, _method in {
    "configure_ontology_project": "configure",
    "prepare_ontology_workload": "prepare",
    "ontology_workflow_status": "status",
    "start_ontology_task": "start_task",
    "record_ontology_task_event": "record_event",
    "finish_ontology_task": "finish_task",
    "execute_ontology_query": "execute_query",
    "resolve_ontology_task": "resolve_task",
    "annotate_ontology_version": "annotate",
}.items():
    _HANDLERS[_tool] = lambda arguments, method=_method: workflow_operation(method, arguments)


def execute(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    handler = _HANDLERS.get(name)
    if handler is None:
        raise ValueError(f"Unknown operation: {name}")
    return handler(arguments or {})
