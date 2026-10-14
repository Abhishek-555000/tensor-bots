# Stage 1: First Agent (Researcher) & CLI Runner

## Goal
Build your first real multi-agent team member: the **Researcher** agent, define the shared `TensorState` dictionary, and run it via the terminal CLI.

---

## What We're Learning
- **`TensorState`**: A `TypedDict` holding the shared state across all agents. With `total=False`, each agent only needs to return keys it modifies.
- **`@agent_node` Decorator**: Automatically emits `agent_started` and `agent_done` lifecycle events, tracks timing, and handles exceptions cleanly.
- **Node Streaming (`graph.stream`)**: Real-time event consumption in `cli.py` using `stream_mode="custom"`.

---

## Architecture in This Stage
```
START ──> [ Researcher ] ──> END
```

---

## How to Test

Run the CLI runner from your terminal:
```bash
python backend/cli.py "Build a pomodoro timer web page"
```

### Expected Output:
```
18:42:01 🚀 RUN STARTED — ID: run_20261014_184201_7a2b
       Prompt: Build a pomodoro timer web page

18:42:01 [RESEARCHER] ⚡ Started work
18:42:01 [RESEARCHER] ⋯ Analyzing tech constraints...
18:42:04 ➔ researcher passed 'Findings' to developer
18:42:04 [RESEARCHER] ✓ Done — Completed research
```

You have a functioning LLM agent communicating structured findings into state! Proceed to **Stage 2** to introduce the **Project Manager**.
