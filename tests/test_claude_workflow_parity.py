from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_claude_build_uses_aggregate_publication_workflow():
    for relative in (
        "plugins/claude-code/skills/evo-build/SKILL.md",
        "plugins/claude-code/commands/evo-build.md",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "annotate_ontology_version" in text
        assert "publish_ontology_build" in text
        assert "set_active_version" not in text


def test_claude_evolve_finalizes_both_terminal_outcomes():
    for relative in (
        "plugins/claude-code/skills/evo-evolve/SKILL.md",
        "plugins/claude-code/commands/evo-evolve.md",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "annotate_ontology_version" in text
        assert "accept_evolution" in text
        assert "finalize_evolution_run" in text
