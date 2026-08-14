"""
Agent registry — the collaboration seam for the swarm.

Each domain agent lives in its own file under `agents/` so teammates can work in
parallel without colliding on one big file. This module discovers those files
and collects their `AGENT` config dicts. `create_specialists.py`,
`upload_skills.py`, and `create_coordinator.py` all read the roster from here.

------------------------------------------------------------------------------
CONTRACT — what an agent file must export
------------------------------------------------------------------------------
Create `agents/<yourname>.py` exporting a module-level dict named `AGENT`:

    AGENT = {
        "key": "nutrition",            # required, unique, snake_case — stable id
        "name": "Nutrition Agent",     # required, human-readable
        "model": "sonnet",             # required, tier alias (see models.py) or full id
        "system": "You are ...",       # required, the system prompt
        "skill": "nutrition-guidelines",  # optional, dir name under skills/ to attach
        "in_coordinator_roster": True, # optional, default True. Onboarding sets False.
    }

Notes:
- `key` is what the coordinator uses to address you and what ids are stored under
  in `.specialist_ids.json`. Don't change it once agents are created.
- `skill` is optional; omit it if your agent runs on prompt rules alone
  (Safety Screener, Synthesis, Onboarding). If set, it must match a directory
  under `skills/` containing a SKILL.md.
- `in_coordinator_roster=False` creates the agent but keeps it OUT of the weekly
  coordinator's callable roster (used for the Onboarding agent, which runs in its
  own `onboard.py` session).
- Files starting with `_` (e.g. `_TEMPLATE.py`) are ignored.

See `agents/_TEMPLATE.py` for a copy-paste starting point.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any

REQUIRED_FIELDS = ("key", "name", "model", "system")


def _validate(agent: dict[str, Any], source: str) -> dict[str, Any]:
    missing = [f for f in REQUIRED_FIELDS if not agent.get(f)]
    if missing:
        raise ValueError(f"agents/{source}.py AGENT is missing required field(s): {missing}")
    agent.setdefault("in_coordinator_roster", True)
    agent.setdefault("skill", None)
    return agent


def load_agents() -> list[dict[str, Any]]:
    """Import every non-underscore module in `agents/` and collect its AGENT dict.

    Returns the agents sorted by key for stable ordering. Raises on duplicate
    keys or malformed configs so mistakes surface loudly at create time.
    """
    import agents  # the package directory

    found: list[dict[str, Any]] = []
    seen_keys: dict[str, str] = {}

    for mod_info in pkgutil.iter_modules(agents.__path__):
        name = mod_info.name
        if name.startswith("_"):
            continue
        module = importlib.import_module(f"agents.{name}")
        agent = getattr(module, "AGENT", None)
        if agent is None:
            # A file in agents/ without an AGENT dict is a soft skip, not an error —
            # lets teammates keep helper modules alongside their agent.
            continue
        agent = _validate(dict(agent), name)
        key = agent["key"]
        if key in seen_keys:
            raise ValueError(
                f"Duplicate agent key '{key}' in agents/{name}.py and "
                f"agents/{seen_keys[key]}.py — keys must be unique."
            )
        seen_keys[key] = name
        found.append(agent)

    return sorted(found, key=lambda a: a["key"])


def roster_keys(agents: list[dict[str, Any]]) -> list[str]:
    """Keys of agents the weekly coordinator can call (excludes onboarding)."""
    return [a["key"] for a in agents if a.get("in_coordinator_roster", True)]
