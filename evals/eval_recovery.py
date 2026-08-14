"""
Correctness evals for the recovery agent output.
"""

import json


def eval_recovery(output: dict, snapshot: dict) -> dict:
    results = {}

    # Sleep target included in recommendation
    recs = " ".join(output.get("recommendations", [])).lower()
    results["sleep_target_included"] = "sleep" in recs and any(
        char.isdigit() for char in recs
    )

    # If any recovery score < 25, a rest day must be recommended
    low_recovery_days = [
        d["date"] for d in snapshot.get("recovery", [])
        if d.get("recovery_score_pct", 100) < 25
    ]
    if low_recovery_days:
        flagged = output.get("low_recovery_days", [])
        results["low_recovery_flagged"] = any(d in flagged for d in low_recovery_days)
        results["low_recovery_days_found"] = low_recovery_days
    else:
        results["low_recovery_flagged"] = True  # no low days, nothing to flag

    passed = all(v for v in results.values() if isinstance(v, bool))
    return {"passed": passed, "details": results}


if __name__ == "__main__":
    with open("synthetic-data/weekly_snapshot.json") as f:
        snapshot = json.load(f)

    sample_output = {
        "recommendations": ["aim for 7.5h sleep Sun through Tue", "take Saturday easy"],
        "low_recovery_days": ["2026-08-16"]
    }

    result = eval_recovery(sample_output, snapshot)
    print(json.dumps(result, indent=2))
