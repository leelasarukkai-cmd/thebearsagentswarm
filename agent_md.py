"""
Parse the agents/<key>/AGENT.md specs into (name, model, system prompt).

Each agent's AGENT.md is the source of truth: the whole file is used as the
agent's system prompt, and the `**Model:**` line sets its model. This keeps the
pipeline scripts (create_agents.py / create_coordinator.py) declarative — add an
agent by adding a folder, no code change.
"""

import re
from pathlib import Path

AGENTS_DIR = Path("agents")


def discover() -> list[str]:
    """All agent keys (folder names) that have an AGENT.md, sorted."""
    if not AGENTS_DIR.exists():
        return []
    return sorted(d.name for d in AGENTS_DIR.iterdir() if (d / "AGENT.md").exists())


def load(key: str) -> dict:
    text = (AGENTS_DIR / key / "AGENT.md").read_text()
    name_m = re.search(r"^#\s+(.+)$", text, re.M)
    model_m = re.search(r"\*\*Model:\*\*\s*`?([\w.\-]+)`?", text)
    return {
        "key": key,
        "name": name_m.group(1).strip() if name_m else key.title(),
        "model": model_m.group(1) if model_m else "claude-sonnet-4-6",
        "system": text,
    }


def specialist_keys() -> list[str]:
    """Every agent except the coordinator (i.e. the ones create_agents.py makes)."""
    return [k for k in discover() if k != "coordinator"]


def coordinator_roster() -> list[str]:
    """Specialists the coordinator fans out to. Onboarding runs upstream (it
    produces the profile) and is not called by the weekly coordinator."""
    return [k for k in specialist_keys() if k != "onboarding"]
