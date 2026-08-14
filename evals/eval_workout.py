"""
Correctness evals for the workout agent output.
"""

import json


def eval_workout(output: dict, profile: dict) -> dict:
    results = {}
    preferred_types = [t.lower() for t in profile["preferred_workout_types"]]
    injury_keywords = [i.split("(")[0].strip().lower() for i in profile["injury_history"]]

    plan = output.get("next_week_plan", {})

    # Workout types match user preferences
    planned_types = [v["type"].lower() for v in plan.values() if "type" in v]
    unknown_types = [t for t in planned_types if not any(p in t for p in preferred_types)]
    results["workout_types_match_preference"] = len(unknown_types) == 0
    if unknown_types:
        results["unexpected_types"] = unknown_types

    # Total weekly duration within range (assumes profile has time_available_min_per_week)
    total_min = sum(v.get("duration_min", 0) for v in plan.values())
    max_min = profile.get("max_weekly_workout_min", 300)
    results["total_duration_within_range"] = total_min <= max_min
    results["total_duration_min"] = total_min

    # No exercises contraindicated by injury history
    all_notes = " ".join(v.get("notes", "") for v in plan.values()).lower()
    injury_violations = [k for k in injury_keywords if k in all_notes]
    results["no_contraindicated_exercises"] = len(injury_violations) == 0

    passed = all(v for v in results.values() if isinstance(v, bool))
    return {"passed": passed, "details": results}


if __name__ == "__main__":
    with open("synthetic-data/user_profile.json") as f:
        profile = json.load(f)

    profile["max_weekly_workout_min"] = 300

    sample_output = {
        "next_week_plan": {
            "monday": {"type": "run", "duration_min": 45, "notes": "easy pace zone 2"},
            "wednesday": {"type": "strength training", "duration_min": 50, "notes": "upper body focus"},
            "friday": {"type": "run", "duration_min": 60, "notes": "tempo run"},
        }
    }

    result = eval_workout(sample_output, profile)
    print(json.dumps(result, indent=2))
