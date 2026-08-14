"""
Create a Recovery Specialist agent for personalized recovery analysis.

This specialist reviews recovery-related data (sleep, HRV, resting heart rate, stress)
for a user and recommends adjustments for the coming week.

The specialist gets:
- A narrow system prompt focused on recovery
- The agent toolset (file ops, web search, web fetch, bash)
- A recovery-playbook skill that matches its domain (uploaded separately)

Saves the resulting agent ID to .recovery_specialist_id.json so other agents
can reference it.

Usage:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python create_recovery_specialist.py
"""

import json
import os
from pathlib import Path

from anthropic import Anthropic


RECOVERY_SPECIALIST = {
    "key": "recovery",
    "name": "Recovery Specialist",
    "model": "claude-haiku-4-5-20251001",
    "system": (
        "You are the Recovery Specialist. You care about the user's recovery and well-being. Your job is to analyze a user's "
        "recovery metrics and recommend adjustments for the coming week.\n\n"
        "Inputs you'll receive:\n"
        "- Weekly recovery snapshot: sleep hours, HRV, resting heart rate, "
        "  strain, recovery scores (from Whoop only)\n"
        "- User profile: schedule constraints, injury history, fitness goals\n"
        "- recovery-playbook skill (your authoritative recovery guidelines)\n\n"
        "Respond with ONLY a single JSON object (no prose before or after, no markdown "
        "code fences) matching exactly this schema:\n"
        "{\n"
        '  "summary": "one sentence on recovery quality this week",\n'
        '  "sleep_avg_hours": 0.0,\n'
        '  "low_recovery_days": ["2026-08-16"],\n'
        '  "recommendations": ["aim for 7.5h sleep Sun-Tue ahead of Wednesday long run"],\n'
        '  "flags": "any concerns for safety screener"\n'
        "}\n\n"
        "Field rules:\n"
        "- summary: one sentence on overall recovery quality and trend (improving/declining/stable)\n"
        "- sleep_avg_hours: the week's average sleep hours, computed from the data\n"
        "- low_recovery_days: every date whose Whoop recovery_score_pct is below 25. "
        "  Empty list if none.\n"
        "- recommendations: specific, numbered-in-spirit actions for next week — always include "
        "  an explicit sleep target in hours per night, and a rest day placement if any day is "
        "  in low_recovery_days\n"
        "- flags: injury or overtraining concerns for the safety team; empty string if none\n\n"
        "Be specific about numbers. Ground every recommendation in the actual data provided. "
        "Never omit a field, and never wrap the JSON in markdown or add explanatory text outside it."
    ),
}


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    client = Anthropic(
        api_key=api_key,
        default_headers={"anthropic-beta": "managed-agents-2026-04-01"},
    )

    agent = client.beta.agents.create(
        name=RECOVERY_SPECIALIST["name"],
        model=RECOVERY_SPECIALIST["model"],
        system=RECOVERY_SPECIALIST["system"],
        tools=[{"type": "agent_toolset_20260401"}],
        metadata={
            "hackathon": "partner-basecamp-2026",
            "track": "specialist-swarm",
            "role": RECOVERY_SPECIALIST["key"],
        },
    )

    specialist_id = agent.id
    print(f"Created {RECOVERY_SPECIALIST['name']:32s} -> {specialist_id}")

    Path(".recovery_specialist_id.json").write_text(
        json.dumps({"recovery": specialist_id}, indent=2)
    )
    print(f"\nSaved specialist ID to .recovery_specialist_id.json")
    print("Next: python upload_skills.py")


if __name__ == "__main__":
    main()
