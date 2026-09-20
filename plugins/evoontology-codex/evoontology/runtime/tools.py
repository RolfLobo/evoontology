"""Shared registries: semantic tools and deterministic build/evolve operations.

``TOOLS`` are the bounded navigation aids a Data Agent uses at query time (and
the visualizer's Tool Layer). ``OPERATIONS`` are the deterministic build,
evolve, validate, visualize, and trigger capabilities exposed through the MCP
server so a plugin-only install never has to run ``python -m evoontology...``
or ``from evoontology import ...`` from the user project.
"""

from __future__ import annotations

_WORKSPACE = {
    "type": "string",
    "description": (
        "Absolute path to the EvoOntology workspace directory "
        "(the .evoontology/ folder under the project root)."
    ),
}

_VISUALIZE_WORKSPACE = {
    "type": "string",
    "description": (
        "Absolute path to an exact EvoOntology workspace, a .evoontology "
        "container, or a project root containing .evoontology. A unique nested "
        "workspace matching the requested version is discovered read-only; pass "
        "the exact workspace when multiple databases match."
    ),
}


TOOLS = [
    {
        "name": "browse_semantics",
        "description": "Discover semantic concepts relevant to an analytical need.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "workspace": _VISUALIZE_WORKSPACE,
                "version": {
                    "type": "string",
                    "description": "Semantic version to browse; omit for the active version.",
                },
                "kind": {
                    "type": "string",
                    "enum": ["term", "mapping", "relation", "constraint", "all"],
                },
                "limit": {"type": "integer", "minimum": 1, "maximum": 6},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "resolve_semantics",
        "description": "Resolve selected concepts to grounded mappings and linked objects.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mentions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 5,
                },
                "context": {"type": "string"},
                "workspace": _VISUALIZE_WORKSPACE,
                "version": {
                    "type": "string",
                    "description": "Semantic version to resolve; omit for the active version.",
                },
            },
            "required": ["mentions"],
            "additionalProperties": False,
        },
    },
]


OPERATIONS = [
    {
        "name": "validate_semantics",
        "description": (
            "Validate an ontology version: required files, JSON validity, "
            "cross-record references, and runtime loadability."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": _WORKSPACE,
                "version": {
                    "type": "string",
                    "description": "Version to validate; omit for the active version.",
                },
            },
            "required": ["workspace"],
            "additionalProperties": False,
        },
    },
    {
        "name": "visualize_ontology",
        "description": (
            "Render every ontology version into one standalone offline HTML explorer "
            "at <workspace>/visualizations/ontology-layer-explorer.html (read-only) and open it in the "
            "default browser automatically unless open_browser is false."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": _VISUALIZE_WORKSPACE,
                "version": {
                    "type": "string",
                    "description": (
                        "Version initially shown in the multi-version explorer; "
                        "omit for the active version."
                    ),
                },
                "presentation": {"type": "string", "enum": ["codex", "external"]},
                "open_browser": {
                    "type": "boolean",
                    "description": (
                        "Open the rendered HTML in the default browser after "
                        "writing it. Defaults to true."
                    ),
                },
            },
            "required": ["workspace"],
            "additionalProperties": False,
        },
    },
    {
        "name": "evolution_status",
        "description": (
            "Idempotently initialize the evolution trigger and report whether "
            "evolution is due (new-trajectory count and elapsed days)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"workspace": _WORKSPACE},
            "required": ["workspace"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_versions",
        "description": "List the active version and all stored ontology versions.",
        "inputSchema": {
            "type": "object",
            "properties": {"workspace": _WORKSPACE},
            "required": ["workspace"],
            "additionalProperties": False,
        },
    },
    {
        "name": "save_version",
        "description": (
            "Persist one ontology version's five record files "
            "(terms/mappings/relations/constraints/evidence)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": _WORKSPACE,
                "version": {"type": "string"},
                "records": {
                    "type": "object",
                    "properties": {
                        "terms": {"type": "array", "items": {"type": "object"}},
                        "mappings": {"type": "array", "items": {"type": "object"}},
                        "relations": {"type": "array", "items": {"type": "object"}},
                        "constraints": {"type": "array", "items": {"type": "object"}},
                        "evidence": {"type": "array", "items": {"type": "object"}},
                    },
                    "required": [
                        "terms",
                        "mappings",
                        "relations",
                        "constraints",
                        "evidence",
                    ],
                },
            },
            "required": ["workspace", "version", "records"],
            "additionalProperties": False,
        },
    },
    {
        "name": "set_active_version",
        "description": "Point active.json at an existing ontology version.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": _WORKSPACE,
                "version": {"type": "string"},
            },
            "required": ["workspace", "version"],
            "additionalProperties": False,
        },
    },
    {
        "name": "start_evolution_run",
        "description": "Create a new evolution run with a frozen round budget.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": _WORKSPACE,
                "parent_version": {"type": "string"},
                "profile": {"type": "string", "enum": ["quick", "full"]},
                "adapter": {"type": "string"},
                "max_rounds": {"type": "integer", "minimum": 1},
                "acceptance": {"type": "object"},
            },
            "required": ["workspace", "parent_version"],
            "additionalProperties": False,
        },
    },
    {
        "name": "resume_evolution_run",
        "description": "Resume the running evolution run, reusing its frozen budget.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": _WORKSPACE,
                "run_id": {"type": "string"},
            },
            "required": ["workspace"],
            "additionalProperties": False,
        },
    },
    {
        "name": "evolution_run_status",
        "description": "Return the latest evolution run record, or null when none exists.",
        "inputSchema": {
            "type": "object",
            "properties": {"workspace": _WORKSPACE},
            "required": ["workspace"],
            "additionalProperties": False,
        },
    },
    {
        "name": "begin_evolution_round",
        "description": "Open the next round for one formal Candidate.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": _WORKSPACE,
                "hypothesis": {"type": "string"},
                "candidate_version": {"type": "string"},
            },
            "required": ["workspace", "hypothesis", "candidate_version"],
            "additionalProperties": False,
        },
    },
    {
        "name": "record_evolution_round",
        "description": "Record a rejected round and keep the run running.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": _WORKSPACE,
                "decision": {"type": "string", "enum": ["reject"]},
                "metrics": {"type": "object"},
                "artifact_refs": {"type": "array", "items": {"type": "string"}},
                "notes": {"type": "string"},
            },
            "required": ["workspace", "decision"],
            "additionalProperties": False,
        },
    },
    {
        "name": "record_evolution_evaluation",
        "description": "Persist a stable summary of a Parent/Candidate evaluation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": _WORKSPACE,
                "subject": {"type": "string"},
                "result": {"type": "object"},
                "role": {"type": "string"},
            },
            "required": ["workspace", "subject", "result"],
            "additionalProperties": False,
        },
    },
    {
        "name": "confirm_trajectory_sources",
        "description": "Persist user-confirmed trajectory source references for a run.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": _WORKSPACE,
                "sources": {
                    "type": "array",
                    "items": {"type": "object"},
                },
            },
            "required": ["workspace", "sources"],
            "additionalProperties": False,
        },
    },
    {
        "name": "accept_evolution",
        "description": (
            "Accept the current Candidate: validate, publish as the next official "
            "version, activate it, and advance the evolution checkpoint."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": _WORKSPACE,
                "new_version": {"type": "string"},
            },
            "required": ["workspace"],
            "additionalProperties": False,
        },
    },
    {
        "name": "mark_evolution_incomplete",
        "description": "End the run for a legitimate external reason.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": _WORKSPACE,
                "reason": {
                    "type": "string",
                    "enum": [
                        "budget_exhausted",
                        "user_interrupted",
                        "missing_data",
                        "missing_permissions",
                        "unreliable_evaluation",
                        "external_block",
                    ],
                },
            },
            "required": ["workspace", "reason"],
            "additionalProperties": False,
        },
    },
    {
        "name": "extend_evolution_budget",
        "description": "Raise the frozen round budget after renewed user confirmation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": _WORKSPACE,
                "max_rounds": {"type": "integer", "minimum": 1},
            },
            "required": ["workspace", "max_rounds"],
            "additionalProperties": False,
        },
    },
    {
        "name": "finalize_evolution_run",
        "description": "Finalize a terminal run and automatically render its outcome explorer. Presentation failures do not change publication status.",
        "inputSchema": {
            "type": "object",
            "properties": {"workspace": _WORKSPACE, "open_browser": {"type": "boolean"}, "presentation": {"type": "string", "enum": ["codex", "external"]}},
            "required": ["workspace"],
            "additionalProperties": False,
        },
    },
]


# Host-agent workflow operations. Questions and tool observations are data, not
# executable instructions; native execution remains in the host except SQLite.
_STRING = {"type": "string"}
_OBJECT = {"type": "object"}
_ARRAY = {"type": "array", "items": {"type": "object"}}

def _workflow_tool(name, description, properties, required=()):
    return {"name": name, "description": description, "inputSchema": {
        "type": "object", "properties": {"workspace": _WORKSPACE, **properties},
        "required": ["workspace", *required], "additionalProperties": False}}

OPERATIONS.extend([
    _workflow_tool("publish_ontology_build", "Validate and activate the initial saved ontology, initialize evolution state and automatically open the outcome explorer. Existing active versions are never overwritten.",
                   {"version": _STRING, "open_browser": {"type": "boolean"}, "presentation": {"type": "string", "enum": ["codex", "external"]}}),
    _workflow_tool("configure_ontology_project", "Persist project context or reuse existing settings. Replace only when reconfiguration was requested.",
                   {"project": _OBJECT, "replace": {"type": "boolean"}}, ["project"]),
    _workflow_tool("prepare_ontology_workload", "Collect project questions by user, same-data history, then evidence-grounded generated questions. Deduplicate and report coverage gaps. Never reads global chat history or reserved benchmark data.",
                   {"questions": _ARRAY, "history": _ARRAY, "generated": _ARRAY,
                    "include_history": {"type": "boolean"},
                    "supplied_only": {"type": "boolean", "description": "Use only questions supplied in this call; retain stored history without selecting it."},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                    "topics": {"type": "array", "items": _STRING}}),
    _workflow_tool("ontology_workflow_status", "Read project context and resumable tasks without changing state.", {}),
    _workflow_tool("start_ontology_task", "Pin a prepared question to an ontology version and start an observable data task. Resume existing running tasks instead of duplicating work.",
                   {"question_id": _STRING, "version": _STRING, "batch_id": _STRING}, ["question_id"]),
    _workflow_tool("record_ontology_task_event", "Record an actual host tool call and result in execution order. Do not submit fabricated observations or hidden reasoning. event_id makes retries idempotent.",
                   {"task_id": _STRING, "tool": _STRING, "arguments": _OBJECT,
                    "result": {}, "event_id": _STRING, "error": {"type": "boolean"}},
                   ["task_id", "tool", "arguments", "result", "event_id"]),
    _workflow_tool("finish_ontology_task", "Finish an executed task and persist its trajectory. Completion is not a correctness judgment.",
                   {"task_id": _STRING, "final_answer": {},
                    "status": {"type": "string", "enum": ["completed", "failed", "interrupted"]}}, ["task_id", "final_answer"]),
    _workflow_tool("execute_ontology_query", "Execute bounded read-only SQL on the task's registered SQLite data source and automatically record its real result. Other databases use host tools plus record_ontology_task_event.",
                   {"task_id": _STRING, "query": _STRING, "event_id": _STRING}, ["task_id", "query", "event_id"]),
    _workflow_tool("resolve_ontology_task", "Resolve concepts against the task's pinned semantic version and record the semantic call without switching the active ontology.",
                   {"task_id": _STRING, "mentions": {"type": "array", "items": _STRING, "maxItems": 5}, "context": _STRING}, ["task_id", "mentions"]),
    _workflow_tool("annotate_ontology_version", "Save a factual version summary, limitations and question-to-object links. Object links are validated; task outcomes come from real trajectories.",
                   {"version": _STRING, "summary": _STRING,
                    "limitations": {"type": "array", "items": _STRING}, "links": _ARRAY},
                   ["version", "summary", "limitations", "links"]),
])
