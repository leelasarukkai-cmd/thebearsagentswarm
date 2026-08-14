# thebearsagentswarm — Text-Based Health Coaching Swarm

A personal health-coaching agent that runs **over texting**. You text it your
week (or it pulls synthetic Garmin / Whoop / MyFitnessPal / Oura exports) and it
texts back concrete, encouraging changes to make next week across **three
domains — nutrition, workouts, recovery — all pointed at one stated goal** (run a
marathon, hold a handstand, finish couch-to-5K, hike the Salkantay trek).

Built on the Claude Managed Agents multi-agent API (`beta.agents` coordinator +
specialists + skills). The texting interface is simulated as a chat loop in the
terminal; real SMS (Twilio) is a stretch goal.

## The swarm

| Agent | Model | Role | Owner |
| --- | --- | --- | --- |
| **Head Coach (coordinator)** | opus | Orchestrates the weekly run; reconciles domain outputs into one coherent reply | infra |
| Nutrition agent | sonnet | Weekly meals + shared shopping list; dietary-aware | teammate |
| Workout agent | sonnet | Next-week training changes toward the goal | teammate |
| Recovery agent | haiku | Sleep + subjective-wellness read; rest guidance | teammate |
| Safety Screener | sonnet | Flags danger (injury/pregnancy/weather/over-reaching); owns the disclaimer | teammate |
| Synthesis agent | sonnet | Formats the reply in a warm texting voice | teammate |
| Onboarding agent | sonnet | Interactive Q&A → `profile.json` (its own session) | teammate |

The coordinator's callable roster is the 5 domain agents (Nutrition, Workout,
Recovery, Safety, Synthesis). The Onboarding agent runs in its own `onboard.py`
session, not called by the weekly coordinator.

## Pipeline

```bash
cd thebearsagentswarm
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."   # workspace key with managed-agents preview access

python setup_environment.py      # .environment_id (idempotent)
python create_specialists.py     # creates every agent in agents/ -> .specialist_ids.json
python upload_skills.py          # uploads + attaches each agent's declared skill (idempotent)
python create_coordinator.py     # wires the coordinator to the roster -> .coordinator_id
python onboard.py                # interactive → profile.json   (owned by onboarding agent)
python run_weekly_checkin.py     # the texting loop → coach texts back
```

The demo is the parallel fan-out: `run_weekly_checkin.py` streams
`[thread spawned] / [thread running] / [reply ←]` for Nutrition + Workout +
Recovery in parallel, then Safety, then Synthesis.

## How to add your agent (teammates)

Every domain agent is one file under `agents/`, discovered automatically — no
central file to edit, so we don't collide.

1. Copy `agents/_TEMPLATE.py` to `agents/<your-agent>.py`.
2. Fill in the `AGENT` dict (`key`, `name`, `model`, `system`, optional `skill`).
   The full contract is documented in `agent_registry.py`.
3. If your agent uses a skill, add `skills/<skill-dir>/SKILL.md` (YAML
   frontmatter: `name` + `description`) and set `"skill": "<skill-dir>"`.
4. Re-run `create_specialists.py` → `upload_skills.py` → `create_coordinator.py`.

The coordinator builds its roster from whatever agents exist, so the pipeline
runs end-to-end even while agents are still landing.

## What's in this repo

**Infrastructure + coordinator (done):**
- `setup_environment.py` — provisions the cloud environment.
- `models.py` — model tier aliases (haiku / sonnet / opus).
- `agent_registry.py` — discovers `agents/*.py`; the collaboration seam.
- `create_specialists.py` — registry-driven agent creation.
- `upload_skills.py` — registry-driven skill upload + attach.
- `create_coordinator.py` — **the coordinator agent** (head-coach prompt + wiring).
- `run_weekly_checkin.py` — the multi-turn texting loop (the demo).
- `schema/ingestion-schema.md` — normalized weekly-record contract.
- `agents/_TEMPLATE.py` — starting point for teammates.

**Owned by teammates (in progress):**
- `agents/{nutrition,workout,recovery,safety,synthesis,onboarding}.py`
- `skills/{nutrition-guidelines,training-periodization,recovery-protocol}/SKILL.md`
- `synthetic-data/*.json` (+ `sample-profile.json`), `onboard.py`

## Design notes

- **Model tiering** — start cheap (haiku), escalate only where reasoning warrants
  (sonnet), reserve opus for the coordinator. Set the tier in each agent file.
- **Restraint is a feature** — not every domain needs a change every week;
  "keep doing exactly what you're doing" is valid output.
- **Not medical advice** — the Safety Screener owns the disclaimer and the coach
  carries it into every reply.

Local artifact files (`.environment_id`, `.specialist_ids.json`, `.coordinator_id`,
etc.) are per-developer and gitignored.
