"""Marketplace manifests and install docs must resolve against this repository.

``claude plugin marketplace add ruc-datalab/EvoOntology`` reads
``.claude-plugin/marketplace.json`` at the repo root and Codex reads
``.agents/plugins/marketplace.json``. Each must be named ``evoontology`` (the part
after ``@`` in the documented install ids) and list the plugin entry the READMEs
tell users to install, pointing at the bundled plugin directory whose own
manifest carries the same name.
"""

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_SLUG = "ruc-datalab/EvoOntology"
MARKETPLACE_NAME = "evoontology"

INSTALL_DOCS = [
    "README.md",
    "README.zh-CN.md",
    "USAGE.md",
    "plugins/claude-code/README.md",
    "plugins/evoontology-codex/README.md",
]
MANIFESTS_WITH_REPO_URLS = [
    "pyproject.toml",
    "plugins/claude-code/.claude-plugin/plugin.json",
    "plugins/evoontology-codex/.codex-plugin/plugin.json",
]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _load_json(path: str) -> dict:
    return json.loads(_read(path))


def _entries(marketplace: dict) -> dict:
    return {entry["name"]: entry for entry in marketplace["plugins"]}


def _assert_inside_repo(relative: str) -> Path:
    assert relative.startswith("./"), relative
    assert ".." not in Path(relative).parts, relative
    target = REPO_ROOT / relative
    assert target.is_dir(), target
    return target


def test_claude_code_marketplace_lists_bundled_plugin():
    marketplace = _load_json(".claude-plugin/marketplace.json")

    assert marketplace["name"] == MARKETPLACE_NAME
    assert marketplace["owner"]["name"]

    entry = _entries(marketplace)["evoontology"]
    plugin_dir = _assert_inside_repo(entry["source"])
    manifest = json.loads(
        (plugin_dir / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    assert manifest["name"] == entry["name"]
    # plugin.json owns the version; declaring it in the entry only produces a warning.
    assert "version" not in entry


def test_codex_marketplace_lists_bundled_plugin():
    marketplace = _load_json(".agents/plugins/marketplace.json")

    assert marketplace["name"] == MARKETPLACE_NAME

    entry = _entries(marketplace)["evoontology-codex"]
    assert entry["source"]["source"] == "local"
    plugin_dir = _assert_inside_repo(entry["source"]["path"])
    manifest = json.loads(
        (plugin_dir / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    assert manifest["name"] == entry["name"]
    assert entry["policy"]["installation"]
    assert entry["policy"]["authentication"]
    assert entry["category"]


@pytest.mark.parametrize("doc", INSTALL_DOCS)
def test_install_docs_add_this_repository_as_marketplace(doc):
    sources = re.findall(r"plugin marketplace add (\S+)", _read(doc))

    assert sources, f"{doc} documents no `plugin marketplace add` command"
    assert set(sources) == {REPO_SLUG}, sources


def test_documented_install_ids_resolve_in_the_marketplaces():
    entries = set(_entries(_load_json(".claude-plugin/marketplace.json")))
    entries |= set(_entries(_load_json(".agents/plugins/marketplace.json")))

    install_ids = set()
    for doc in INSTALL_DOCS:
        install_ids |= set(re.findall(r"plugin (?:install|add) (\S+)@(\S+)", _read(doc)))

    assert install_ids, "no documented `plugin install <name>@<marketplace>` command"
    for plugin, marketplace in install_ids:
        assert marketplace == MARKETPLACE_NAME, (plugin, marketplace)
        assert plugin in entries, (plugin, sorted(entries))


@pytest.mark.parametrize("manifest", MANIFESTS_WITH_REPO_URLS)
def test_manifests_link_to_this_repository(manifest):
    text = _read(manifest)

    assert f"github.com/{REPO_SLUG}" in text
    assert "MeiduoChong/EvoOntology" not in text
