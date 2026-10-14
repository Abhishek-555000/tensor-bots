# Stage 2: Manager Agent & Structured Briefs

## Goal
Implement the **Project Manager** agent using Groq's structured output capability (`with_structured_output`) to parse the user request into role-specific briefs for the crew.

---

## What We're Learning
- **Pydantic Schemas (`AgentBriefs`)**: Enforcing strict JSON schema responses from the LLM.
- **Structured LLM (`llm.with_structured_output`)**: Guaranteeing that the model produces strongly typed fields for each team member.
- **Sequential Edges (`START -> manager -> researcher`)**: Chaining agents where subsequent agents read inputs produced by earlier agents in `state["briefs"]`.

---

## Architecture in This Stage
```
START ──> [ Project Manager ] ──> [ Researcher ] ──> END
```

---

## How to Test

Run the CLI runner from your terminal:
```bash
python backend/cli.py "Build a pomodoro timer web page"
```

### Expected Output:
```
18:45:10 🚀 RUN STARTED — ID: run_20261014_184510_8f1c
       Prompt: Build a pomodoro timer web page

18:45:10 [ MANAGER  ] ⚡ Started work
18:45:10 [ MANAGER  ] ⋯ Decomposing user request...
18:45:10 [DEVELOPER ] ⏳ Waiting on: researcher, planner
18:45:10 [ REVIEWER ] ⏳ Waiting on: developer
18:45:13 ➔ manager passed 'Research brief' to researcher
18:45:13 [ MANAGER  ] ✓ Done — Dispatched briefs
18:45:13 [RESEARCHER] ⚡ Started work
18:45:13 [RESEARCHER] ⋯ Analyzing tech constraints...
18:45:16 ➔ researcher passed 'Findings' to developer
18:45:16 [RESEARCHER] ✓ Done — Researcher completed task.
```

The Project Manager has successfully broken down the goal into structured briefs! Proceed to **Stage 3** to run the **Planner** concurrently with the **Researcher**.
