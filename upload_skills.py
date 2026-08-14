"""
Upload each skill declared by an agent and attach it to that agent.

The skill -> agent mapping is derived from the registry: any agent file that
sets `"skill": "<dir-name>"` gets that skill (from skills/<dir-name>/) uploaded
and attached. No hardcoded map to keep in sync.

Uses `files_from_dir` to package the skill directory. Each skill bundle must
contain a SKILL.md at its root with YAML frontmatter (`name` + `description`).

Idempotent: reuses an already-uploaded skill by title and skips re-attaching.

Usage:
    python upload_skills.py
"""

import json
import os
from pathlib import Path

from anthropic import Anthropic
from anthropic.lib import files_from_dir

from agent_registry import load_agents


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    specialist_ids_path = Path(".specialist_ids.json")
    if not specialist_ids_path.exists():
        raise SystemExit("Run create_specialists.py first.")
    specialist_ids = json.loads(specialist_ids_path.read_text())

    # skill dir name -> agent key, from whichever agents declare a skill
    skill_to_specialist = {
        a["skill"]: a["key"] for a in load_agents() if a.get("skill")
    }
    if not skill_to_specialist:
        print("No agents declare a skill yet — nothing to upload.")
        print("Next: python create_coordinator.py")
        return

    client = Anthropic()

    # List existing custom skills so we can detect and reuse any prior uploads.
    # Skills API enforces unique display_title, so retrying with the same title
    # would otherwise fail. Idempotent retry is essential for hackathon dev loops.
    print("Checking for existing skills...")
    existing_by_title: dict[str, str] = {}
    for page in client.beta.skills.list(source="custom"):
        existing_by_title[page.display_title] = page.id

    uploaded: dict[str, str] = {}

    for skill_name, specialist_key in skill_to_specialist.items():
        skill_dir = Path("skills") / skill_name
        if not (skill_dir / "SKILL.md").exists():
            print(f"  Skipping {skill_name} — no skills/{skill_name}/SKILL.md found")
            continue
        if specialist_key not in specialist_ids:
            print(f"  Skipping {skill_name} — agent '{specialist_key}' not created yet")
            continue

        display_title = skill_name.replace("-", " ").title()

        # 1. Upload the skill (or reuse if one already exists with this title)
        if display_title in existing_by_title:
            skill_id = existing_by_title[display_title]
            print(f"Reusing existing skill: {skill_name} ({skill_id})")
            uploaded[skill_name] = skill_id
        else:
            print(f"Uploading skill: {skill_name}...")
            skill = client.beta.skills.create(
                display_title=display_title,
                files=files_from_dir(str(skill_dir)),
            )
            uploaded[skill_name] = skill.id
            print(f"  -> {skill.id}")

        # 2. Attach to the matching agent by updating its skills array
        specialist_id = specialist_ids[specialist_key]
        skill_id = uploaded[skill_name]
        print(f"  attaching to agent `{specialist_key}` ({specialist_id})...")

        current = client.beta.agents.retrieve(specialist_id)
        already_attached = any(
            s.get("skill_id") == skill_id for s in (current.skills or [])
        )
        if already_attached:
            print("  already attached ✓ (skipping)")
            continue

        new_skills = list(current.skills or []) + [
            {"type": "custom", "skill_id": skill_id, "version": "latest"}
        ]
        client.beta.agents.update(
            specialist_id,
            version=current.version,
            skills=new_skills,
        )
        print("  attached ✓")

    Path(".skill_ids.json").write_text(json.dumps(uploaded, indent=2))
    print(f"\nUploaded {len(uploaded)} skill(s) and attached them to agents.")
    print("Next: python create_coordinator.py")


if __name__ == "__main__":
    main()
