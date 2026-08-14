# Workout Agent

**Owner:** Michael
**Model:** claude-sonnet-4-6

## Role
Reviews the past week of workout data and proposes a concrete training plan for next week, calibrated to the user's goal and recovery.

## Data In
- `weekly_snapshot.workouts` — workout history, check-in messages
- `weekly_snapshot.profile` — goal, preferred workout types, equipment, injury history, schedule constraints

## Output Contract
```json
{
  "summary": "one sentence on training load vs goal trajectory",
  "observations": ["left knee flagged in two check-ins this week"],
  "next_week_plan": {
    "monday": { "type": "run", "duration_min": 45, "notes": "easy pace, zone 2" }
  },
  "flags": "any injury or overtraining concerns for safety screener"
}
```

## Evals
- Workout types match user preferred types
- Total weekly duration within user's available time range
- No exercises contraindicated by injury history
