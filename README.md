# Milo — Personal Health Coaching Agent

A multi-agent health coach that texts you concrete changes to make next week across nutrition, workouts, and recovery — all pointed at one stated goal.

**Trigger:** Every Sunday at 4pm PST

---

## Architecture

```
Onboarding Agent
      ↓
[Apple Health / Garmin / Whoop / Oura / MyFitnessPal]
      ↓
  normalize.py → weekly_snapshot.json
      ↓
┌─────────────────────────────────┐
│  Nutrition Agent (Sonnet)       │  → Shane
│  Workout Agent (Sonnet)         │  → Michael
│  Recovery Agent (Haiku)         │  → Salma
└─────────────────────────────────┘
      ↓
  Safety Screener
      ↓
  Synthesis Agent (Sonnet)        → Eva
      ↓
  Coordinator Agent (Opus)        → Leela
      ↓
  Text to user
```

---

## Agents

| Agent | Owner | Model | Data In |
|-------|-------|-------|---------|
| Onboarding | — | Sonnet | — |
| Nutrition | Shane | Sonnet | `nutrition` + `profile` |
| Workout | Michael | Sonnet | `workouts` + `profile` |
| Recovery | Salma | Haiku | `recovery` + `profile` |
| Safety Screener | Leela | Haiku | All agent outputs |
| Synthesis | Eva | Sonnet | Full `weekly_snapshot.json` |
| Coordinator | Leela | Opus | All agent outputs |

Each agent has its own folder under `agents/` with an `AGENT.md` describing its system prompt and I/O contract.

---

## Setup

```bash
cd thebearsagentswarm
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."   # or put it in a .env file — it's auto-loaded
```

## Run

```bash
python normalize.py          # merge sources/ → weekly_snapshot.json
python create_agents.py      # create specialist agents
python create_coordinator.py # create coordinator
python run_milo.py           # run the full pipeline
```

---

## Folder Structure

```
thebearsagentswarm/
├── agents/
│   ├── onboarding/AGENT.md
│   ├── nutrition/AGENT.md
│   ├── workout/AGENT.md
│   ├── recovery/AGENT.md
│   ├── safety/AGENT.md
│   ├── synthesis/AGENT.md
│   └── coordinator/AGENT.md
├── synthetic-data/
│   ├── sources/             # raw per-platform exports
│   │   ├── apple_health.json
│   │   ├── garmin.json
│   │   ├── whoop.json
│   │   ├── oura.json
│   │   └── myfitnesspal.json
│   ├── user_profile.json    # onboarding output
│   └── weekly_snapshot.json # normalized input for agents
├── evals/
│   ├── eval_nutrition.py
│   ├── eval_workout.py
│   ├── eval_recovery.py
│   └── eval_tone.py
├── normalize.py
├── agent_md.py                 # parses agents/*/AGENT.md → model + system prompt
├── create_agents.py
├── create_coordinator.py
├── run_milo.py
└── requirements.txt
```
