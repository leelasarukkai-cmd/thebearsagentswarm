"""
normalize.py — merges raw source files into a single weekly_snapshot.json.

Preferred source per metric is set in user_profile.json under preferred_data_sources.
Where sources overlap (e.g. sleep from both Oura and Whoop), the preferred source wins.

Usage:
    python normalize.py
"""

import json
from pathlib import Path

SOURCES_DIR = Path("synthetic-data/sources")
PROFILE_PATH = Path("synthetic-data/user_profile.json")
OUTPUT_PATH = Path("synthetic-data/weekly_snapshot.json")


def load(filename: str) -> dict:
    path = SOURCES_DIR / filename
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def normalize() -> None:
    profile = json.loads(PROFILE_PATH.read_text())
    preferred = profile.get("preferred_data_sources", {})

    garmin = load("garmin.json")
    whoop = load("whoop.json")
    oura = load("oura.json")
    mfp = load("myfitnesspal.json")

    # Workouts — preferred: garmin
    workouts = garmin.get("workouts", [])

    # Recovery — Whoop only (recovery_score_pct isn't present in Oura's schema)
    recovery = whoop.get("daily", [])

    # Sleep — preferred: oura
    sleep_source = oura if preferred.get("sleep") == "oura" else whoop
    sleep = [
        {
            "date": d["date"],
            "sleep_total_hours": d.get("sleep_total_hours"),
            "sleep_deep_hours": d.get("sleep_deep_hours"),
            "sleep_rem_hours": d.get("sleep_rem_hours"),
            "sleep_efficiency_pct": d.get("sleep_efficiency_pct"),
            "readiness_score": d.get("readiness_score"),
            "hrv_balance": d.get("hrv_balance"),
        }
        for d in sleep_source.get("daily", [])
    ]

    # Nutrition — preferred: myfitnesspal
    nutrition = mfp.get("daily", [])

    snapshot = {
        "week_of": garmin.get("week_of") or whoop.get("week_of") or mfp.get("week_of"),
        "profile": profile,
        "workouts": workouts,
        "recovery": recovery,
        "sleep": sleep,
        "nutrition": nutrition,
    }

    OUTPUT_PATH.write_text(json.dumps(snapshot, indent=2))
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    normalize()
