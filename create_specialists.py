"""
Create the domain sub-agents for the health-coach swarm.

Agents are discovered from the `agents/` directory via agent_registry.py — one
file per agent so teammates can add theirs without colliding here. Each agent
gets its narrow system prompt and the agent toolset; skills are attached later
by upload_skills.py.

Saves the resulting agent ids to .specialist_ids.json so create_coordinator.py
can reference them.

Usage:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python create_specialists.py
"""

import json
import os
from pathlib import Path

from anthropic import Anthropic

from agent_registry import load_agents
from models import resolve


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    agents = load_agents()
    if not agents:
        raise SystemExit(
            "No agents found in agents/. Each teammate adds agents/<name>.py "
            "(see agents/_TEMPLATE.py and agent_registry.py)."
        )

    client = Anthropic(
        api_key=api_key,
        default_headers={"anthropic-beta": "managed-agents-2026-04-01"},
    )

    specialist_ids: dict[str, str] = {}
    for spec in agents:
        agent = client.beta.agents.create(
            name=spec["name"],
            model=resolve(spec["model"]),
            system=spec["system"],
            tools=[{"type": "agent_toolset_20260401"}],
            metadata={
                "hackathon": "partner-basecamp-2026",
                "track": "health-coach-swarm",
                "role": spec["key"],
            },
        )
        specialist_ids[spec["key"]] = agent.id
        roster = "" if spec["in_coordinator_roster"] else "  (not in coordinator roster)"
        print(f"  Created {spec['name']:28s} -> {agent.id}{roster}")

    Path(".specialist_ids.json").write_text(json.dumps(specialist_ids, indent=2))
    print(f"\nSaved {len(specialist_ids)} agent id(s) to .specialist_ids.json")
    print("Next: python upload_skills.py")


if __name__ == "__main__":
    main()
