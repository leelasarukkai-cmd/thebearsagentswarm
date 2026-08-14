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
        "  stress levels, recovery scores (from Whoop/Oura)\n"
        "- User profile: schedule constraints, injury history, fitness goals\n"
        "- recovery-playbook skill (your authoritative recovery guidelines)\n\n"
        "Your output: a one-paragraph recovery recommendation covering:\n"
        "1. Recovery quality summary for the past week\n"
        "2. Average sleep hours and trend (improving/declining/stable)\n"
        "3. Any days with critically low recovery (score < 25%)\n"
        "4. Specific, actionable recommendations for next week:\n"
        "   - Sleep target (hours per night)\n"
        "   - Rest day placement if needed\n"
        "   - HRV or stress management tactics\n"
        "5. Safety flags for the coaching team (injury concerns, overtraining)\n\n"
        "Be specific about numbers. Ground recommendations in the actual data "
        "provided. Flag anything unusual or concerning for the safety team."
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
