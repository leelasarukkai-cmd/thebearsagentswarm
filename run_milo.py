"""
Run Milo — the weekly texting loop.

Sends the normalized weekly_snapshot.json as the user's first "text", then
streams the coordinator's swarm so you can watch the parallel fan-out (Nutrition
+ Workout + Recovery in parallel, then Safety, then Synthesis) — the parallelism
is the demo. After Milo "texts back", the loop stays open so you can reply and
iterate in the same session.

Provisions the cloud environment on first run (idempotent via .environment_id).

Usage:
    python normalize.py     # first, to produce weekly_snapshot.json
    python run_milo.py
"""

import os
from pathlib import Path

from anthropic import Anthropic


SNAPSHOT_PATH = Path("synthetic-data/weekly_snapshot.json")

KICKOFF = (
    "Based on the past week of workouts, nutrition, and recovery, please "
    "recommend changes to make next week to each to meet my stated goal."
)


def ensure_environment(client: Anthropic) -> str:
    env_path = Path(".environment_id")
    if env_path.exists():
        return env_path.read_text().strip()
    print("Provisioning cloud environment...")
    environment = client.beta.environments.create(
        name="milo-env",
        config={"type": "cloud", "networking": {"type": "unrestricted"}},
    )
    env_path.write_text(environment.id)
    print(f"  environment: {environment.id}")
    return environment.id


def stream_turn(client: Anthropic, session_id: str, text: str) -> None:
    print("\n--- Milo is thinking (watch the parallel fan-out) ---\n")
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
                    print("\n=== MILO (text back) ===\n", flush=True)
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

    if not Path(".coordinator_id").exists():
        raise SystemExit(
            "Missing .coordinator_id. Run create_agents.py then create_coordinator.py first."
        )
    if not SNAPSHOT_PATH.exists():
        raise SystemExit(f"Missing {SNAPSHOT_PATH}. Run `python normalize.py` first.")

    coordinator_id = Path(".coordinator_id").read_text().strip()
    snapshot = SNAPSHOT_PATH.read_text()

    client = Anthropic()
    environment_id = ensure_environment(client)

    print(f"\nStarting texting session against Milo {coordinator_id}...")
    session = client.beta.sessions.create(
        agent=coordinator_id,
        environment_id=environment_id,
        title="Milo — Weekly Check-in",
    )
    Path(".last_session_id").write_text(session.id)

    first_text = (
        f"{KICKOFF}\n\n"
        "===== THIS WEEK'S DATA (weekly_snapshot.json — includes my profile) =====\n"
        f"{snapshot}"
    )
    stream_turn(client, session.id, first_text)

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
    print(f"  https://platform.claude.com/sessions/{session.id}")


if __name__ == "__main__":
    main()
