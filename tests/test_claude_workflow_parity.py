from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_claude_build_uses_aggregate_publication_workflow():
    text = (ROOT / "plugins/claude-code/skills/build-ontology/SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "annotate_ontology_version" in text
    assert "publish_ontology_build" in text
    assert "set_active_version" not in text
    assert "references/workload-experience.md" in text


def test_claude_evolve_finalizes_both_terminal_outcomes():
    text = (ROOT / "plugins/claude-code/skills/evolve-ontology/SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "annotate_ontology_version" in text
    assert "accept_evolution" in text
    assert "finalize_evolution_run" in text
    assert "result.gate_input" in text


def test_claude_plugin_uses_skills_without_legacy_commands():
    commands = ROOT / "plugins/claude-code/commands"
    assert not commands.exists() or not any(commands.iterdir())
