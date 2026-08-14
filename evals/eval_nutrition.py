"""
Correctness evals for the nutrition agent output.

Three checks, matching agents/nutrition/AGENT.md:
  1. Plan macros within ±5% of profile targets
  2. Zero restricted ingredients (in the shopping list OR the proposed meals)
  3. Shopping list reuses ingredients across >=3 meals
"""

import json
import re

# A restriction is written for a human ("no shellfish"), so a substring match
# against an ingredient never fires. Map each restriction to the words that
# actually appear in a meal or shopping list.
RESTRICTION_TERMS = {
    "shellfish": ["shrimp", "prawn", "crab", "lobster", "scallop", "clam",
                  "mussel", "oyster", "crayfish", "langoustine"],
    "peanut": ["peanut"],
    "tree nut": ["almond", "cashew", "walnut", "pecan", "pistachio", "hazelnut"],
    "dairy": ["milk", "cheese", "yogurt", "yoghurt", "butter", "cream"],
    "gluten": ["bread", "pasta", "flour", "wheat", "barley", "couscous", "cracker"],
    "egg": ["egg"],
    "soy": ["soy", "tofu", "edamame", "tempeh", "miso"],
    "pork": ["pork", "bacon", "ham", "prosciutto", "chorizo"],
    "beef": ["beef", "steak"],
    "vegetarian": ["chicken", "beef", "steak", "pork", "bacon", "turkey", "lamb",
                   "salmon", "tuna", "cod", "fish", "shrimp"],
    "pescatarian": ["chicken", "beef", "steak", "pork", "bacon", "turkey", "lamb"],
    "vegan": ["chicken", "beef", "pork", "turkey", "fish", "salmon", "egg",
              "milk", "cheese", "yogurt", "butter", "cream", "honey"],
}


def banned_terms(restrictions: list[str]) -> list[str]:
    """Turn profile restriction phrases into concrete ingredient words."""
    terms = []
    for restriction in restrictions:
        text = restriction.lower()
        matched = False
        for key, words in RESTRICTION_TERMS.items():
            if key in text:
                terms.extend(words)
                matched = True
        if not matched:
            # Unknown restriction — fall back to its own words, minus the "no".
            terms.extend(w for w in re.findall(r"[a-z]+", text) if w not in {"no", "free"})
    return sorted(set(terms))


def meal_strings(output: dict) -> list[str]:
    """Every proposed meal as a lowercase string."""
    meals = []
    for day in (output.get("next_week_meals") or {}).values():
        if isinstance(day, dict):
            meals.extend(str(v).lower() for v in day.values() if v)
        elif day:
            meals.append(str(day).lower())
    return meals


def eval_nutrition(output: dict, profile: dict) -> dict:
    results = {}
    targets = profile["macro_targets"]
    restrictions = profile.get("dietary_restrictions", [])

    # 1. Plan macros within ±5% of target
    for macro in ["protein_g", "carbs_g", "fat_g"]:
        if macro in targets and macro in output:
            delta = abs(output[macro] - targets[macro]) / targets[macro]
            results[f"{macro}_within_5pct"] = delta <= 0.05

    # 2. Zero restricted ingredients — check the shopping list AND the meals,
    #    since a restricted item can appear in a meal without being listed.
    banned = banned_terms(restrictions)
    haystack = [str(i).lower() for i in output.get("shopping_list", [])] + meal_strings(output)
    violations = sorted({term for term in banned for item in haystack if term in item})
    results["no_restricted_ingredients"] = not violations
    if violations:
        results["restriction_violations"] = violations

    # 3. Shopping list reuse — at least one ingredient in >=3 proposed meals
    meals = meal_strings(output)
    reuse = {
        item: sum(1 for meal in meals if item in meal)
        for item in (str(i).lower() for i in output.get("shopping_list", []))
    }
    reused = {k: v for k, v in reuse.items() if v >= 3}
    results["shopping_list_reused_across_3_meals"] = bool(reused)
    if reused:
        results["most_reused"] = sorted(reused.items(), key=lambda kv: -kv[1])[:5]

    passed = all(v for v in results.values() if isinstance(v, bool))
    return {"passed": passed, "details": results}


if __name__ == "__main__":
    with open("synthetic-data/user_profile.json") as f:
        profile = json.load(f)

    # Replace with actual agent output when available.
    sample_output = {
        "protein_g": 148,
        "carbs_g": 198,
        "fat_g": 64,
        "next_week_meals": {
            "monday": {"breakfast": "oats with berries", "lunch": "salmon rice bowl",
                       "snack": "greek yogurt", "dinner": "salmon and broccoli"},
            "tuesday": {"breakfast": "oats with banana", "lunch": "lentil salad",
                        "snack": "greek yogurt", "dinner": "shrimp stir fry"},
        },
        "shopping_list": ["salmon", "brown rice", "broccoli", "oats", "greek yogurt"],
    }

    result = eval_nutrition(sample_output, profile)
    print(json.dumps(result, indent=2))
