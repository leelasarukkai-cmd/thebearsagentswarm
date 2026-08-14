# Coordinator Agent

**Owner:** Leela
**Model:** claude-opus-4-7

## Role
Orchestrates the full pipeline. Fans work out to specialist agents in parallel, collects their outputs, passes to safety screener, then synthesis agent, and delivers the final text to the user.

## Responsibilities
1. Load `weekly_snapshot.json` and route slices to each specialist
2. Run nutrition, workout, recovery agents in parallel
3. Pass all outputs to safety screener
4. Pass screened outputs to synthesis agent
5. Deliver final text message to user

## Pipeline Order
```
[nutrition, workout, recovery] → parallel
         ↓
    safety screener
         ↓
    synthesis agent
         ↓
    final text to user
```
