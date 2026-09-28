"""Canonical EvoOntology workspace resolution and project context storage."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Dict, Optional, Union

PathLike = Union[str, Path]
WORKSPACE_DIRNAME = ".evoontology"
PROJECT_SCHEMA_VERSION = 1
PROJECT_MODES = {"fixed_split", "rolling_trajectory"}


def validate_path_component(value: Any, *, label: str = "identifier") -> str:
    """Return one safe path component without imposing a naming convention."""
    if value is None:
        raise ValueError(f"{label} must be a single path component")
    text = str(value)
    windows = PureWindowsPath(text)
    if (
        not text
        or text in {".", ".."}
        or "\x00" in text
        or "/" in text
        or "\\" in text
        or PurePosixPath(text).is_absolute()
        or bool(windows.drive)
        or bool(windows.root)
    ):
        raise ValueError(f"{label} must be a single path component")
    return text


def resolve_workspace(
    workspace: Optional[PathLike] = None,
    *,
    project_root: Optional[PathLike] = None,
) -> Path:
    """Return an absolute workspace path.

    An explicit ``workspace`` takes precedence. Otherwise the default is
    ``<project_root>/.evoontology`` and ``project_root`` defaults to the
    current working directory.
    """
    if workspace is not None:
        return Path(workspace).expanduser().resolve()
    root = Path(project_root) if project_root is not None else Path.cwd()
    return (root.expanduser().resolve() / WORKSPACE_DIRNAME)


def resolve_workspace_for_version(
    workspace: Optional[PathLike] = None,
    *,
    project_root: Optional[PathLike] = None,
    version: str = "active",
) -> Path:
    """Find one existing workspace that can serve a read-only version request.

    ``workspace`` may name the final workspace, a ``.evoontology`` container
    holding database-specific workspaces, or a project root containing such a
    container. Direct matches win. A unique nested match is discovered at any
    depth; ambiguous matches raise instead of selecting an arbitrary database.

    This resolver never creates or modifies workspace state. Write operations
    must continue to use :func:`resolve_workspace` with an exact destination.
    """
    requested = str(version or "active").strip() or "active"
    requested = validate_path_component(requested, label="version")
    root = resolve_workspace(workspace, project_root=project_root)
    if _workspace_has_version(root, requested):
        return root

    nested_container = root / WORKSPACE_DIRNAME
    search_root = nested_container if nested_container.is_dir() else root
    if not search_root.is_dir():
        return search_root

    if requested == "active":
        possible = {path.parent for path in search_root.rglob("active.json")}
    else:
        possible = {path.parent for path in search_root.rglob("versions")}
    candidates = sorted(
        {
            candidate.resolve()
            for candidate in possible
            if _workspace_has_version(candidate, requested)
        },
        key=lambda path: str(path).casefold(),
    )
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        listed = "\n".join(f"- {path}" for path in candidates)
        raise ValueError(
            f"Multiple EvoOntology workspaces match version {requested!r} under "
            f"{search_root}:\n{listed}\nPass the exact workspace path."
        )
    return search_root


def _workspace_has_version(root: Path, version: str) -> bool:
    version = validate_path_component(version, label="version")
    if version != "active":
        return (root / "versions" / version).is_dir()
    active_file = root / "active.json"
    if not active_file.is_file():
        return False
    try:
        active = json.loads(active_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(active, dict):
        return False
    active_version = str(
        active.get("active_version") or active.get("version") or ""
    ).strip()
    if not active_version:
        return False
    try:
        active_version = validate_path_component(
            active_version, label="active version"
        )
    except ValueError:
        return False
    return (root / "versions" / active_version).is_dir()


def ensure_workspace(
    workspace: Optional[PathLike] = None,
    *,
    project_root: Optional[PathLike] = None,
) -> Path:
    """Create the idempotent workspace directory skeleton.

    State-bearing JSON files are written only when their corresponding
    lifecycle step completes: Step 0 writes ``project.json``; publication
    writes ``active.json`` and initializes ``state.json``.
    """
    root = resolve_workspace(workspace, project_root=project_root)
    for directory in ("versions", "trajectories", "evolution"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    return root


def load_project(
    workspace: Optional[PathLike] = None,
    *,
    project_root: Optional[PathLike] = None,
) -> Dict[str, Any]:
    """Load and minimally validate ``<workspace>/project.json``."""
    root = resolve_workspace(workspace, project_root=project_root)
    path = root / "project.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing EvoOntology project context: {path}")
    try:
        project = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid project.json: {exc}") from exc
    return _validate_project(project)


def save_project(
    project: Dict[str, Any],
    workspace: Optional[PathLike] = None,
    *,
    project_root: Optional[PathLike] = None,
) -> Path:
    """Validate and atomically persist ``project.json``."""
    normalized = _validate_project(project)
    root = ensure_workspace(workspace, project_root=project_root)
    path = root / "project.json"
    temporary = root / "project.json.tmp"
    temporary.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)
    return path


def _validate_project(project: Any) -> Dict[str, Any]:
    if not isinstance(project, dict):
        raise ValueError("project.json must contain a JSON object")
    schema_version = project.get("schema_version", project.get("version"))
    if schema_version != PROJECT_SCHEMA_VERSION:
        raise ValueError(
            f"project.json schema_version must be {PROJECT_SCHEMA_VERSION}"
        )
    mode = project.get("mode")
    if mode not in PROJECT_MODES:
        raise ValueError(f"project.json mode must be one of {sorted(PROJECT_MODES)}")
    for field in ("data_source", "workload_source", "evaluation", "boundary"):
        if field not in project:
            raise ValueError(f"project.json is missing required field: {field}")
    for field in ("evaluation", "boundary"):
        if not isinstance(project[field], dict):
            raise ValueError(f"project.json field {field!r} must be an object")
    normalized = dict(project)
    normalized.pop("version", None)
    normalized["schema_version"] = PROJECT_SCHEMA_VERSION
    return normalized
