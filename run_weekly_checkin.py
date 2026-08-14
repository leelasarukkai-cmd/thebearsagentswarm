"""
Weekly check-in — the texting loop.

Bundles the user's profile.json + the week's synthetic device data + the kickoff
prompt as the first "text", then streams the coordinator's swarm so you can watch
the parallel fan-out (Nutrition + Workout + Recovery in parallel, then Safety,
then Synthesis) — the parallelism is the demo, narrate it live. After the coach
"texts back", the loop stays open so you can reply and iterate in the same
session (e.g. "I only have 3 days next week").

Usage:
    python run_weekly_checkin.py
"""

import os
from pathlib import Path

from anthropic import Anthropic


PROFILE_PATH = Path("profile.json")
SAMPLE_PROFILE_PATH = Path("synthetic-data/sample-profile.json")
DATA_DIR = Path("synthetic-data")

# The coach's kickoff prompt (per the team brainstorm).
KICKOFF = (
    "Based on the past week of workouts, nutrition, and recovery, please "
    "recommend changes to make next week to each to meet my stated goal."
)


def load_profile() -> str:
    """Prefer the onboarded profile.json; fall back to a committed sample."""
    for path in (PROFILE_PATH, SAMPLE_PROFILE_PATH):
        if path.exists():
            print(f"  profile: {path}")
            return path.read_text()
    print("  WARNING: no profile.json or sample-profile.json — run onboard.py first.")
    return "(no profile provided)"


def load_week_data() -> str:
    """Inline every synthetic export in synthetic-data/ (skip the sample profile)."""
    blocks: list[str] = []
    if not DATA_DIR.exists():
        print(f"  WARNING: {DATA_DIR}/ missing — no week data to send.")
        return "(no weekly data provided)"
    for path in sorted(DATA_DIR.glob("*.json")):
        if path.name == SAMPLE_PROFILE_PATH.name:
            continue
        print(f"  data: {path.name}")
        blocks.append(f"=====  {path.name}  =====\n{path.read_text()}")
    if not blocks:
        print(f"  WARNING: no *.json exports in {DATA_DIR}/.")
        return "(no weekly data provided)"
    return "\n\n".join(blocks)


def build_first_text(profile: str, week_data: str) -> str:
    return (
        f"{KICKOFF}\n\n"
        "===== MY PROFILE (goal + constraints) =====\n"
        f"{profile}\n\n"
        "===== THIS WEEK'S DATA (from my devices/apps) =====\n"
        f"{week_data}"
    )


def stream_turn(client: Anthropic, session_id: str, text: str) -> None:
    """Send one user 'text' and stream the swarm's response to stdout."""
    print("\n--- coach is thinking (watch the parallel fan-out) ---\n")
    with client.beta.sessions.events.stream(session_id) as stream:
        client.beta.sessions.events.send(
            session_id,
            events=[{"type": "user.message", "content": [{"type": "text", "text": text}]}],
        )
        printed_reply_header = False
        for event in stream:
            t = event.type
            if t == "session.thread_created":
                print(f"  [thread spawned]   {event.agent_name}", flush=True)
            elif t == "session.thread_status_running":
                print(f"  [thread running]   {getattr(event, 'agent_name', '?')}", flush=True)
            elif t == "agent.thread_message_sent":
                print(f"  [delegate →]       {event.to_agent_name}", flush=True)
            elif t == "agent.thread_message_received":
                print(f"  [reply ←]          {event.from_agent_name}", flush=True)
            elif t == "agent.message":
                if not printed_reply_header:
                    print("\n=== COACH (text back) ===\n", flush=True)
                    printed_reply_header = True
                for block in event.content:
                    if getattr(block, "type", None) == "text":
                        print(block.text, end="", flush=True)
            elif t == "session.status_idle":
                print("\n", flush=True)
                break


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    if not Path(".coordinator_id").exists() or not Path(".environment_id").exists():
        raise SystemExit(
            "Missing .coordinator_id or .environment_id. Run setup_environment.py, "
            "create_specialists.py, upload_skills.py, then create_coordinator.py first."
        )

    coordinator_id = Path(".coordinator_id").read_text().strip()
    environment_id = Path(".environment_id").read_text().strip()

    client = Anthropic()

    print("Loading profile + this week's data...")
    profile = load_profile()
    week_data = load_week_data()

    print(f"\nStarting texting session against coach {coordinator_id}...")
    session = client.beta.sessions.create(
        agent=coordinator_id,
        environment_id=environment_id,
        title="Health Coach — Weekly Check-in",
    )
    Path(".last_session_id").write_text(session.id)

    # First "text": profile + week data + kickoff prompt.
    stream_turn(client, session.id, build_first_text(profile, week_data))

    # Multi-turn texting loop — reply and iterate, blank line or 'exit' to quit.
    print("--- reply to keep texting (blank line or 'exit' to finish) ---")
    while True:
        try:
            reply = input("you > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not reply or reply.lower() in {"exit", "quit", "bye"}:
            break
        stream_turn(client, session.id, reply)

    print(f"\nSession saved: {session.id}")
    print("View the full session (including all sub-agent threads) at:")
    print(f"  https://platform.claude.com/sessions/{session.id}")


if __name__ == "__main__":
    main()
