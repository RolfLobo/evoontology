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
        skill = _read(root / ("build-ontology" if "evoontology-codex" in str(root) else "evo-build") / "SKILL.md")
        boundary = _read(
            root / ("build-ontology" if "evoontology-codex" in str(root) else "evo-build") / "references" / "ontology-layer-data-boundary.md"
        )
        assert "Fixed-Split Mode" in skill
        assert "Rolling-Trajectory Mode" in skill
        assert "fixed_split" in boundary
        assert "rolling_trajectory" in boundary
        assert (root / ("build-ontology" if "evoontology-codex" in str(root) else "evo-build") / "references" / "project-context.md").is_file()


def test_evolve_skill_documents_both_modes():
    for root in SKILL_ROOTS:
        skill = _read(root / ("evolve-ontology" if "evoontology-codex" in str(root) else "evo-evolve") / "SKILL.md")
        boundary = _read(
            root / ("evolve-ontology" if "evoontology-codex" in str(root) else "evo-evolve") / "references" / "ontology-layer-data-boundary.md"
        )
        assert "Fixed-Split Mode" in skill
        assert "Rolling-Trajectory Mode" in skill
        assert "fixed_split" in boundary
        assert "rolling_trajectory" in boundary
