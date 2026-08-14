# Onboarding Agent

**Model:** claude-sonnet-4-6

## Role
Gathers the user's profile once via conversational chat (text-style). Saves output to `user_profile.json`.

## Questions to cover
1. What's your goal? (be specific — "run a marathon," "do a handstand")
2. What types of workouts do you enjoy? What equipment do you have?
3. Any dietary restrictions or strong food preferences?
4. How many meals a day do you want planned? (breakfast / snack / lunch / dinner)
5. Any injuries or health history I should know about?
6. What does your weekly schedule look like? Any days/times that are off-limits?
7. Which apps/wearables do you use? (Apple Health, Garmin, Whoop, Oura, MyFitnessPal)

## Output
Saves a `user_profile.json` matching the schema in `synthetic-data/user_profile.json`.
