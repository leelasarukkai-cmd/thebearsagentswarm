"""
Correctness evals for the synthesis agent output.

Two checks, matching agents/synthesis/AGENT.md (tone score is a separate
LLM-as-judge check — see eval_tone.py):
  1. All three agent domains addressed in changes_next_week
  2. No contradictions between domains (e.g. don't recommend a high-strain
     workout on a flagged low-recovery day)
"""

import json
import re

DOMAINS = ["nutrition", "workouts", "recovery"]

# Recovery output (or a safety flag) says "protect recovery" — workouts
# shouldn't simultaneously read as "push harder."
RESTRAINT_TERMS = [
    "hold", "rest", "ease", "easy", "reduce", "lower", "back off",
    "protect recovery", "recovery day", "deload", "scale back", "cut back",
]
ESCALATION_TERMS = [
    "increase", "add volume", "more volume", "ramp up", "push harder",
    "higher intensity", "high intensity", "high-strain", "harder effort",
    "add a tempo", "add an interval", "longer run", "extra session",
]


def _contains_term(text: str, term: str) -> bool:
    """Whole-word/phrase match so e.g. 'ease' doesn't false-match inside 'increase'."""
    return re.search(r"\b" + re.escape(term) + r"\b", text) is not None


def _domain_items(output: dict, domain: str) -> list[str]:
    items = (output.get("changes_next_week") or {}).get(domain, [])
    return [str(i) for i in items if str(i).strip()]


def _recovery_is_flagged(recovery_output: dict | None, safety_output: dict | None) -> bool:
    if recovery_output and recovery_output.get("low_recovery_days"):
        return True
    for flag in (safety_output or {}).get("flags", []):
        domain = str(flag.get("domain", "")).lower()
        issue = str(flag.get("issue", "")).lower()
        if domain in {"recovery", "cross-domain"} and (
            "overtrain" in issue or "recovery" in issue
        ):
            return True
    return False


def eval_synthesis(output: dict, recovery_output: dict = None, safety_output: dict = None) -> dict:
    results = {}

    # 1. All three domains addressed — each must have at least one concrete item.
    empty_domains = [d for d in DOMAINS if not _domain_items(output, d)]
    results["all_domains_addressed"] = not empty_domains
    if empty_domains:
        results["empty_domains"] = empty_domains

    # 2. No contradictions — if recovery is flagged (low recovery day, or an
    #    overtraining/recovery flag from the safety screener), the workouts
    #    changes shouldn't read as an escalation with no restraint language.
    if _recovery_is_flagged(recovery_output, safety_output):
        workout_text = " ".join(_domain_items(output, "workouts")).lower()
        has_escalation = any(_contains_term(workout_text, term) for term in ESCALATION_TERMS)
        has_restraint = any(_contains_term(workout_text, term) for term in RESTRAINT_TERMS)
        contradiction = has_escalation and not has_restraint
        results["no_workout_recovery_contradiction"] = not contradiction
        if contradiction:
            results["contradiction_detail"] = (
                "recovery flagged but workouts changes read as an escalation "
                "with no restraint language"
            )
    else:
        results["no_workout_recovery_contradiction"] = True

    passed = all(v for v in results.values() if isinstance(v, bool))
    return {"passed": passed, "details": results}


if __name__ == "__main__":
    # Clean case: recovery is fine, workouts can progress.
    clean_output = {
        "weekly_summary": "Solid week — training and nutrition both tracked toward the half marathon.",
        "changes_next_week": {
            "nutrition": ["add a protein shake Mon/Tue to close the 32g gap"],
            "workouts": ["add a tempo segment to Friday's run"],
            "recovery": ["keep the current 7h sleep target"],
        },
        "progress_note": "20.2km this week keeps you on pace for December.",
        "ready_for_coordinator": True,
    }
    print("clean case:")
    print(json.dumps(eval_synthesis(clean_output), indent=2))

    # Contradiction case: recovery flagged low, but workouts still escalate.
    contradiction_output = dict(clean_output)
    contradiction_output["changes_next_week"] = {
        "nutrition": ["add a protein shake Mon/Tue to close the 32g gap"],
        "workouts": ["increase Friday's tempo run and add an extra session"],
        "recovery": ["watch Saturday's low recovery score"],
    }
    recovery_output = {"low_recovery_days": ["2026-08-16"]}
    print("\ncontradiction case:")
    print(json.dumps(eval_synthesis(contradiction_output, recovery_output=recovery_output), indent=2))
