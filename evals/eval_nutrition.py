"""
Correctness evals for the nutrition agent output.
"""

import json


def eval_nutrition(output: dict, profile: dict) -> dict:
    results = {}
    targets = profile["macro_targets"]
    restrictions = profile["dietary_restrictions"]

    # Macro targets within ±5%
    for macro in ["protein_g", "carbs_g", "fat_g"]:
        if macro in targets and macro in output:
            delta = abs(output[macro] - targets[macro]) / targets[macro]
            results[f"{macro}_within_5pct"] = delta <= 0.05

    # Zero restricted ingredients
    all_ingredients = output.get("shopping_list", [])
    violations = [i for i in all_ingredients if any(r.lower() in i.lower() for r in restrictions)]
    results["no_restricted_ingredients"] = len(violations) == 0
    if violations:
        results["restriction_violations"] = violations

    passed = all(v for v in results.values() if isinstance(v, bool))
    return {"passed": passed, "details": results}


if __name__ == "__main__":
    with open("synthetic-data/user_profile.json") as f:
        profile = json.load(f)

    # Replace with actual agent output when available
    sample_output = {
        "protein_g": 148,
        "carbs_g": 198,
        "fat_g": 64,
        "shopping_list": ["chicken breast", "salmon", "brown rice", "broccoli", "oats"]
    }

    result = eval_nutrition(sample_output, profile)
    print(json.dumps(result, indent=2))
