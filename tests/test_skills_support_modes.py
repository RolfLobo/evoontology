"""Regression test: build/evolve skills support both modes in both plugins."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOTS = [
    REPO_ROOT / "plugins" / "claude-code" / "skills",
    REPO_ROOT / "plugins" / "evoontology-codex" / "skills",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_build_skill_documents_both_modes():
    for root in SKILL_ROOTS:
        skill = _read(root / "build-ontology" / "SKILL.md")
        boundary = _read(
            root / "build-ontology" / "references" / "ontology-layer-data-boundary.md"
        )
        assert "Fixed-Split Mode" in skill
        assert "Rolling-Trajectory Mode" in skill
        assert "fixed_split" in boundary
        assert "rolling_trajectory" in boundary
        assert (root / "build-ontology" / "references" / "project-context.md").is_file()
        assert (root / "build-ontology" / "references" / "workload-experience.md").is_file()


def test_evolve_skill_documents_both_modes():
    for root in SKILL_ROOTS:
        skill = _read(root / "evolve-ontology" / "SKILL.md")
        boundary = _read(
            root / "evolve-ontology" / "references" / "ontology-layer-data-boundary.md"
        )
        assert "Fixed-Split Mode" in skill
        assert "Rolling-Trajectory Mode" in skill
        assert "fixed_split" in boundary
        assert "rolling_trajectory" in boundary


def test_both_plugins_expose_the_same_workflow_names():
    expected = {"build-ontology", "evolve-ontology", "explore-ontology"}
    for root in SKILL_ROOTS:
        assert {path.name for path in root.iterdir() if path.is_dir()} == expected
        for name in expected:
            assert f"name: {name}" in _read(root / name / "SKILL.md")
