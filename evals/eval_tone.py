"""
LLM-as-judge tone eval for the synthesis/coordinator agent output.
"""

import json
import os
import re
from anthropic import Anthropic

JUDGE_PROMPT = """You are evaluating the output of a health coaching AI. Score it on four dimensions, each 1-5. Be honest — a lenient score on a mediocre output is a failure of the eval.

USER CONTEXT:
{user_profile}

AGENT OUTPUT TO EVALUATE:
{agent_output}

SCORING RUBRIC:

1. DIRECTNESS (1-5)
   5 — States the recommendation in the first sentence. No hedging.
   3 — Gets there eventually but buries it in qualifications.
   1 — Uses phrases like "you might consider" or "it could be worth exploring."
   Automatic 1 if output contains: "consider", "perhaps", "might want to", "it may help to."

2. KINDNESS (1-5)
   5 — Acknowledges something specific the user did well before corrections. Frames every gap as fixable.
   3 — Neutral tone, neither warm nor harsh.
   1 — Shaming, guilt-inducing, or cold.
   Automatic 1 if output contains: "you failed", "you didn't", "you should have."

3. SPECIFICITY (1-5)
   5 — Every recommendation cites a specific data point from this user's week.
   3 — Some specifics, some generic advice.
   1 — Advice that could apply to any person regardless of their data.
   Automatic 1 if no user data is referenced anywhere in the output.

4. CONCISENESS (1-5)
   5 — No filler. Gets to the point within the first two sentences.
   3 — Some filler but recovers quickly.
   1 — Opens with hollow affirmations or spends more than 2 sentences before making a point.
   Automatic 1 if output opens with "Great,", "Amazing,", "Fantastic,", or "Awesome,".

Return JSON only. No explanation outside the JSON block.

{{
  "directness": {{ "score": 0, "reason": "one sentence" }},
  "kindness":   {{ "score": 0, "reason": "one sentence" }},
  "specificity": {{ "score": 0, "reason": "one sentence" }},
  "conciseness": {{ "score": 0, "reason": "one sentence" }},
  "overall": 0.0,
  "pass": false
}}

"overall" is the average of the four scores, rounded to one decimal.
"pass" is true if overall >= 4.0 AND no dimension scored below 3."""


def eval_tone(agent_output: str, profile: dict) -> dict:
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = JUDGE_PROMPT.format(
        user_profile=json.dumps(profile, indent=2),
        agent_output=agent_output,
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    # Judge sometimes wraps the JSON in a ```json ... ``` fence despite being
    # told not to — strip it before parsing.
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.IGNORECASE)
    return json.loads(raw)


if __name__ == "__main__":
    with open("synthetic-data/user_profile.json") as f:
        profile = json.load(f)

    sample_output = (
        "Protein came in 32g under target Monday through Wednesday — "
        "add a scoop of protein powder to breakfast those days and you're there. "
        "Saturday's recovery score hit 43, so Sunday is a walk, not a run. "
        "You put in 20.2km this week. That's real half-marathon progress."
    )

    result = eval_tone(sample_output, profile)
    print(json.dumps(result, indent=2))
