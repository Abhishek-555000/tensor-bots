# Stage 3: Parallel Fan-Out and Join

## Goal
Implement concurrent execution in LangGraph: the **Project Manager** fans out tasks to **Researcher** and **Planner** in parallel, and both branches join into the **Developer** node.

---

## What We're Learning
- **Parallel Fan-Out**: Adding multiple outgoing edges from one node (`manager -> researcher` and `manager -> planner`).
- **Fan-In / Join Barrier**: Using a list in `add_edge(["researcher", "planner"], "developer")` so LangGraph automatically waits for both tasks to complete before firing the Developer.
- **State Merging**: How LangGraph merges state updates from concurrent nodes without race conditions when nodes modify distinct keys (`research` and `plan`).

---

## Architecture in This Stage
```
                   ┌─> [ Researcher ] ─┐
START ──> [ Manager ]                  ├─> [ Developer (Stub) ] ──> END
                   └─> [  Planner   ] ─┘
```

---

## How to Test

Run the CLI runner from your terminal:
```bash
python backend/cli.py "Build a pomodoro timer web page"
```

### Expected Output:
```
18:48:02 🚀 RUN STARTED — ID: run_20261014_184802_3d1a
       Prompt: Build a pomodoro timer web page

18:48:02 [ MANAGER  ] ⚡ Started work
18:48:02 [ MANAGER  ] ⋯ Decomposing user request...
18:48:02 [DEVELOPER ] ⏳ Waiting on: researcher, planner
18:48:02 [ REVIEWER ] ⏳ Waiting on: developer
18:48:05 ➔ manager passed 'Research brief' to researcher
18:48:05 [ MANAGER  ] ✓ Done — Dispatched briefs
18:48:05 [RESEARCHER] ⚡ Started work
18:48:05 [RESEARCHER] ⋯ Analyzing tech constraints...
18:48:05 [ PLANNER  ] ⚡ Started work
18:48:05 [ PLANNER  ] ⋯ Drafting architecture plan...
18:48:08 ➔ researcher passed 'Findings' to developer
18:48:08 [RESEARCHER] ✓ Done — Researcher completed task.
18:48:09 ➔ planner passed 'Specs' to developer
18:48:09 [ PLANNER  ] ✓ Done — Planner completed task.
18:48:09 [DEVELOPER ] ⚡ Started work
18:48:09 [DEVELOPER ] ⋯ Gathered inputs from Researcher and Planner...
18:48:09 [DEVELOPER ] ✓ Done — Developer stub completed.
```

Parallel execution and state joining work smoothly! Proceed to **Stage 4** to give the Developer real sandboxed file-writing tools.
