#!/usr/bin/env python3
"""Session-start evolution reminder hook.

Checks ``<cwd>/.evoontology`` for an evolution-due condition and prints a
one-line reminder to stdout. Claude Code injects hook stdout into the session
context, so the agent sees the reminder without any user action.

Silently exits when no ontology layer is active or when evolution is not due.
For backward compatibility, an active legacy workspace without ``state.json``
is initialized automatically before checking its trajectories.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evoontology import EvolutionTrigger, resolve_workspace


def main() -> int:
    base = resolve_workspace()  # <cwd>/.evoontology

    roots: list[Path] = []
    if (base / "active.json").is_file():
        roots.append(base)
    for active_path in sorted(base.glob("*/active.json")):
        roots.append(active_path.parent)

    reminders: list[str] = []
    for root in roots:
        trigger = EvolutionTrigger(str(root))
        trigger.initialize()
        result = trigger.check()
        if result["evolution_due"]:
            label = root.name if root != base else "workspace"
            reminders.append(
                f"EvoOntology: evolution is due ({result['reason']}) for {label}. "
                f"Run /evoontology:evolve-ontology to review and improve the ontology layer."
            )

    if not reminders:
        return 0

    context = (
        "The EvoOntology layer has pending evolution work.\n"
        + "\n".join(reminders)
    )
    visible_message = "\n".join(reminders)
    print(
        json.dumps(
            {
                # additionalContext is deliberately hidden from the terminal;
                # systemMessage makes the due reminder visible to the user.
                "systemMessage": visible_message,
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": context,
                }
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
