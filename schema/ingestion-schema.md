# Ingestion schema — the normalized weekly record

The point of the integration story is that many device/app exports (Garmin,
Whoop, Oura, MyFitnessPal, Apple Health, manual check-ins) all normalize into
**one weekly record** the coordinator and specialists reason over. This doc is
the contract: source files live in `synthetic-data/`, and each source maps into
the shape below.

The current runner (`run_weekly_checkin.py`) inlines every `synthetic-data/*.json`
verbatim into the first "text", so a strict normalized JSON file is not yet
required to demo. This schema defines the target shape for whoever builds the
synthetic exports and (stretch) a real normalizer.

## Normalized weekly record

```jsonc
{
  "week_of": "2026-08-04",              // ISO date, Monday of the week

  "workouts": [                          // from Garmin / Apple Health / Strava
    {
      "date": "2026-08-05",
      "type": "run | strength | walk | hike | mobility | cross | rest",
      "duration_min": 42,
      "distance_km": 6.1,                // null for non-distance workouts
      "avg_hr": 148,                     // null if not measured
      "elevation_gain_m": 30,            // null if flat / not measured
      "perceived_effort": 6,             // 1-10, from checkins if present
      "notes": "easy pace, tight calves"
    }
  ],

  "recovery": {                          // from Whoop / Oura / Apple Health
    "avg_sleep_hours": 6.8,
    "sleep_consistency": "low | moderate | high",
    "avg_hrv_ms": 42,                    // null if not measured
    "avg_resting_hr": 58,
    "recovery_scores": [55, 60, 48, 72], // daily 0-100, device-native; null-ok
    "subjective_wellness": {             // from checkins.json
      "mood": "low | ok | good",
      "stress": "low | moderate | high",
      "soreness": "none | mild | notable"
    }
  },

  "nutrition": {                         // from MyFitnessPal / manual
    "avg_daily_calories": 2180,
    "avg_daily_protein_g": 96,
    "avg_daily_carbs_g": 240,
    "avg_daily_fat_g": 78,
    "meals_logged_days": 5,              // out of 7 — logging adherence
    "notes": "weekend eating out, low protein midweek"
  }
}
```

## Source → normalized mapping

| Source file (`synthetic-data/`) | Feeds | Normalized fields |
| --- | --- | --- |
| `garmin-workouts.json` | Workout agent | `workouts[]` |
| `whoop-recovery.json` | Recovery agent | `recovery.*` (sleep, HRV, scores) |
| `myfitnesspal-nutrition.json` | Nutrition agent | `nutrition.*` |
| `checkins.json` | Recovery + Safety | `workouts[].perceived_effort`, `recovery.subjective_wellness` |
| `sample-profile.json` | all (goal + constraints) | not part of the weekly record — the persistent profile |

## Profile (separate from the weekly record)

`profile.json` is produced once by the onboarding flow and read every week. Shape
(the onboarding agent owns the authoritative version):

```jsonc
{
  "goal": "run a sub-4:30 marathon in 12 weeks",
  "workout_preferences": ["running", "gym strength"],
  "dietary": { "restrictions": [], "preferences": [], "meals_per_day": 3 },
  "sleep_baseline_hours": 7,
  "schedule_constraints": "desk job, can train ~4 days/week, mornings",
  "injuries_history": ["occasional tight calves"],
  "pregnancy": false,
  "equipment": ["running shoes", "commercial gym"],
  "subjective_baseline": "moderate, inconsistent activity"
}
```

A committed `synthetic-data/sample-profile.json` in this shape gives a fast demo
path when nobody has run `onboard.py` yet.
