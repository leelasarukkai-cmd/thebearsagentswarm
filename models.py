"""
Friendly model aliases for the swarm.

Agent files declare a tier ("haiku" / "sonnet" / "opus") instead of hard-coding
a versioned model id, so we can bump every agent's model in one place. The ids
below are the ones proven to work against the `managed-agents-2026-04-01` beta.

Model tiering is a feature of this project: start cheap (haiku), escalate only
where the reasoning warrants it (sonnet), reserve opus for the coordinator.
"""

MODELS = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-7",
}


def resolve(model: str) -> str:
    """Map a tier alias to a concrete model id. Pass-through for full ids."""
    return MODELS.get(model, model)
