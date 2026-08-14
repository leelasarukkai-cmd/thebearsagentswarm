"""
TEMPLATE — copy this file to agents/<your-agent>.py and fill in AGENT.

Files starting with `_` are ignored by the registry, so this template never
gets created as a real agent. Delete these instructions in your copy.

Full contract lives in ../agent_registry.py.
"""

AGENT = {
    # Stable snake_case id. The coordinator addresses you by this; agent ids are
    # stored under it in .specialist_ids.json. Don't change it after first create.
    "key": "example",

    # Human-readable name shown in the event stream.
    "name": "Example Agent",

    # Model tier: "haiku" (cheap), "sonnet" (default), or "opus". Start cheap and
    # escalate only if the reasoning needs it. See ../models.py.
    "model": "sonnet",

    # Narrow system prompt. State the agent's job, the inputs it receives (weekly
    # data + profile), and the exact shape of the output the coordinator should get.
    "system": (
        "You are the Example Agent. Replace this with a narrow, specific prompt.\n"
        "Keep your reply to one message, concrete and actionable."
    ),

    # OPTIONAL — dir name under skills/ to attach (must contain SKILL.md).
    # Omit or set None if you run on prompt rules alone.
    "skill": None,

    # OPTIONAL — default True. Set False only for the Onboarding agent, which runs
    # in its own onboard.py session rather than being called by the coordinator.
    "in_coordinator_roster": True,
}
