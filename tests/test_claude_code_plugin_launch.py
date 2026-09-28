import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
PLUGIN = ROOT / "plugins" / "claude-code"
LAUNCHER = PLUGIN / "scripts" / "launch-evoontology"


def test_claude_mcp_and_hook_share_cross_platform_launcher():
    mcp = json.loads((PLUGIN / ".mcp.json").read_text(encoding="utf-8"))
    server = mcp["mcpServers"]["evo-semantic"]
    assert server == {
        "command": "bash",
        "args": ["${CLAUDE_PLUGIN_ROOT}/scripts/launch-evoontology", "mcp"],
    }

    hooks = json.loads((PLUGIN / "hooks/hooks.json").read_text(encoding="utf-8"))
    hook = hooks["hooks"]["SessionStart"][0]["hooks"][0]
    assert hook["command"] == "bash"
    assert hook["args"] == [
        "${CLAUDE_PLUGIN_ROOT}/scripts/launch-evoontology",
        "reminder",
    ]


def test_launcher_answers_initialize_and_tools_list_from_foreign_cwd(tmp_path):
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is unavailable")
    requests = "\n".join(
        [
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18"},
                }
            ),
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
            "",
        ]
    )
    env = dict(os.environ)
    env.pop("EVO_ONTOLOGY_PYTHON", None)
    completed = subprocess.run(
        [bash, str(LAUNCHER), "mcp"],
        cwd=tmp_path,
        env=env,
        input=requests,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    responses = [json.loads(line) for line in completed.stdout.splitlines()]
    assert responses[0]["result"]["protocolVersion"] == "2025-06-18"
    names = {tool["name"] for tool in responses[1]["result"]["tools"]}
    assert {"save_version", "publish_ontology_build", "accept_evolution"} <= names


def test_launcher_runs_reminder_from_foreign_cwd(tmp_path):
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is unavailable")
    completed = subprocess.run(
        [bash, str(LAUNCHER), "reminder"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    assert completed.stdout == ""
