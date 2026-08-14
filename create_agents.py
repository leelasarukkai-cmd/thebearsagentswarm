"""
Create the specialist sub-agents from their agents/<key>/AGENT.md specs.

Reads every agent folder except `coordinator/` (that's created by
create_coordinator.py). Each agent's full AGENT.md is its system prompt and its
`**Model:**` line sets the model. Saves the resulting ids to
.specialist_ids.json so create_coordinator.py can wire them up.

Usage:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python create_agents.py
"""

import json
import os
from pathlib import Path

from anthropic import Anthropic

from agent_md import load, specialist_keys


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    keys = specialist_keys()
    if not keys:
        raise SystemExit("No agents found under agents/*/AGENT.md.")

    client = Anthropic(
        default_headers={"anthropic-beta": "managed-agents-2026-04-01"},
    )

    specialist_ids: dict[str, str] = {}
    for key in keys:
        spec = load(key)
        agent = client.beta.agents.create(
            name=spec["name"],
            model=spec["model"],
            system=spec["system"],
            tools=[{"type": "agent_toolset_20260401"}],
            metadata={
                "hackathon": "partner-basecamp-2026",
                "track": "milo",
                "role": key,
            },
        )
        specialist_ids[key] = agent.id
        print(f"  Created {spec['name']:24s} ({spec['model']:22s}) -> {agent.id}")

    Path(".specialist_ids.json").write_text(json.dumps(specialist_ids, indent=2))
    print(f"\nSaved {len(specialist_ids)} agent id(s) to .specialist_ids.json")
    print("Next: python create_coordinator.py")


if __name__ == "__main__":
    main()
