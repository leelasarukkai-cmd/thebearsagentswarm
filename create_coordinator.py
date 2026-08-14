"""
Create the coordinator agent (Milo) from agents/coordinator/AGENT.md.

Wires the coordinator to the specialists it fans out to — the roster is every
created specialist except onboarding (which runs upstream to produce the
profile). Reads .specialist_ids.json written by create_agents.py and saves the
coordinator id to .coordinator_id.

Usage:
    python create_coordinator.py
"""

import json
import os
from pathlib import Path

from anthropic import Anthropic

from agent_md import coordinator_roster, load

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    ids_path = Path(".specialist_ids.json")
    if not ids_path.exists():
        raise SystemExit("Run create_agents.py first.")
    specialist_ids = json.loads(ids_path.read_text())

    # Roster = intended fan-out agents that were actually created. Excluding any
    # not-yet-created agents lets this run while teammates' agents are still landing.
    wanted = coordinator_roster()
    roster = [k for k in wanted if k in specialist_ids]
    missing = [k for k in wanted if k not in specialist_ids]
    if missing:
        print(f"  NOTE: roster agents not created yet, excluding: {missing}")
    if not roster:
        raise SystemExit("No roster specialists available — run create_agents.py.")

    spec = load("coordinator")
    client = Anthropic(
        default_headers={"anthropic-beta": "managed-agents-2026-04-01"},
    )

    coordinator = client.beta.agents.create(
        name=spec["name"],
        model=spec["model"],
        system=spec["system"],
        tools=[{"type": "agent_toolset_20260401"}],
        multiagent={
            "type": "coordinator",
            "agents": [
                {"type": "agent", "id": specialist_ids[key]} for key in roster
            ],
        },
        metadata={
            "hackathon": "partner-basecamp-2026",
            "track": "milo",
            "role": "coordinator",
        },
    )

    Path(".coordinator_id").write_text(coordinator.id)
    print(f"Coordinator created: {coordinator.id}  ({spec['model']})")
    print(f"Roster ({len(roster)}): {roster}")
    print("\nNext: python run_milo.py")


if __name__ == "__main__":
    main()
