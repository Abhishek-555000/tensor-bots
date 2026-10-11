"""
Stage 1-5: CLI Runner for Tensor Bots
-------------------------------------
Executes the full LangGraph multi-agent graph from the command line and
pretty-prints real-time events as they stream from the custom event writer.
# TEACH: `graph.stream(initial_state, stream_mode="custom")` streams custom events
# directly as nodes call `get_stream_writer()`.
Usage:
    python cli.py "Build a pomodoro timer web page"
"""

import sys
import time
import uuid
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import WORKSPACE_DIR
from app.events import emit
from app.graph import graph


# ANSI color codes for terminal formatting
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "cyan": "\033[36m",
    "magenta": "\033[35m",
    "yellow": "\033[33m",
    "green": "\033[32m",
    "blue": "\033[34m",
    "red": "\033[31m",
}

AGENT_COLORS = {
    "manager": COLORS["magenta"],
    "researcher": COLORS["cyan"],
    "planner": COLORS["blue"],
    "developer": COLORS["yellow"],
    "reviewer": COLORS["green"],
}


def format_agent(name: str) -> str:
    col = AGENT_COLORS.get(name.lower(), COLORS["cyan"])
    return f"{col}[{name.upper():^10}]{COLORS['reset']}"


def print_event(event: dict):
    """Pretty-print an event object in a concise, readable single line."""
    etype = event.get("type", "")
    ts = time.strftime("%H:%M:%S", time.localtime(event.get("ts", time.time())))
    prefix = f"{COLORS['dim']}{ts}{COLORS['reset']}"

    if etype == "run_started":
        print(f"\n{prefix} {COLORS['bold']}🚀 RUN STARTED{COLORS['reset']} — ID: {event.get('run_id')}")
        print(f"       Prompt: {COLORS['bold']}{event.get('prompt')}{COLORS['reset']}\n")

    elif etype == "agent_started":
        agent = event.get("agent", "")
        print(f"{prefix} {format_agent(agent)} ⚡ Started work")

    elif etype == "agent_status":
        agent = event.get("agent", "")
        text = event.get("text", "")
        print(f"{prefix} {format_agent(agent)} ⋯ {text}")

    elif etype == "agent_waiting":
        agent = event.get("agent", "")
        on = ", ".join(event.get("on", []))
        print(f"{prefix} {format_agent(agent)} ⏳ Waiting on: {on}")

    elif etype == "handoff":
        src = event.get("from", "")
        dst = event.get("to", "")
        lbl = event.get("label", "")
        print(f"{prefix} ➔ {COLORS['bold']}{src}{COLORS['reset']} passed '{lbl}' to {COLORS['bold']}{dst}{COLORS['reset']}")

    elif etype == "file_written":
        agent = event.get("agent", "developer")
        path = event.get("path", "")
        nbytes = event.get("bytes", 0)
        print(f"{prefix} {format_agent(agent)} 📝 Wrote {COLORS['green']}{path}{COLORS['reset']} ({nbytes} bytes)")

    elif etype == "review_verdict":
        approved = event.get("approved", False)
        iteration = event.get("iteration", 1)
        tag = f"{COLORS['green']}APPROVED ✓{COLORS['reset']}" if approved else f"{COLORS['yellow']}CHANGES REQUESTED ↺{COLORS['reset']}"
        print(f"{prefix} {format_agent('reviewer')} ⚖ Verdict (Round {iteration}): {tag}")

    elif etype == "agent_done":
        agent = event.get("agent", "")
        summary = event.get("summary", "")
        print(f"{prefix} {format_agent(agent)} ✓ Done — {summary}")

    elif etype == "run_finished":
        files = event.get("files", [])
        print(f"\n{prefix} {COLORS['bold']}{COLORS['green']}🏁 RUN COMPLETED{COLORS['reset']}")
        print(f"       Deliverables ({len(files)} files):")
        for f in files:
            print(f"       • {f}")
        print(f"\n{COLORS['dim']}{event.get('summary', '')}{COLORS['reset']}\n")

    elif etype == "run_error":
        msg = event.get("message", "Unknown error")
        print(f"{prefix} {COLORS['red']}[ERROR]{COLORS['reset']} {msg}")


def run_cli(prompt: str):
    run_id = f"run_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
    run_dir = WORKSPACE_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    initial_state = {
        "run_id": run_id,
        "user_prompt": prompt,
        "iteration": 0,
        "files": [],
    }

    # Emit run_started event
    start_event = emit("run_started", run_id=run_id, prompt=prompt)
    print_event(start_event)

    try:
        # Stream custom events as nodes produce them
        for event in graph.stream(initial_state, stream_mode="custom"):
            if isinstance(event, dict):
                print_event(event)
    except Exception as exc:
        err_event = emit("run_error", message=str(exc))
        print_event(err_event)
        raise


if __name__ == "__main__":
    prompt_arg = sys.argv[1] if len(sys.argv) > 1 else "Build a pomodoro timer web page"
    run_cli(prompt_arg)
