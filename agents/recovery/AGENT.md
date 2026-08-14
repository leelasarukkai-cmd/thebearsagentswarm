# Recovery Agent

**Owner:** Salma
**Model:** claude-haiku-4-5-20251001

## Role
Reviews sleep and recovery data from the past week and recommends changes for next week.

## Data In
- `weekly_snapshot.recovery` — HRV, sleep hours, recovery scores (Whoop/Oura)
- `weekly_snapshot.profile` — goal, schedule constraints

## Output Contract
```json
{
  "summary": "one sentence on recovery quality this week",
  "sleep_avg_hours": 0.0,
  "low_recovery_days": ["2026-08-16"],
  "recommendations": ["aim for 7.5h sleep Sun-Tue ahead of Wednesday long run"],
  "flags": "any concerns for safety screener"
}
```

## Evals
- Sleep target (hours) included in recommendation
- If any day's recovery score < 25 (Whoop or Oura readiness), rest day recommended
