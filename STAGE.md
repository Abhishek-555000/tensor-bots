# Stage 5: Reviewer Agent, Conditional Loop & Final Delivery

## Goal
Close the loop by adding the **Reviewer** agent, implementing a **Conditional Edge** that routes between iteration revisions and completion, and finishing with the **Project Manager**'s final delivery summary.

---

## What We're Learning
- **Conditional Routing (`workflow.add_conditional_edges`)**: Dynamic decision trees in LangGraph based on runtime state values (`approved: bool`, `iteration >= MAX_REVIEW_ROUNDS`).
- **Loop Guardrails**: Protecting against infinite loops using `MAX_REVIEW_ROUNDS` (default `2`).
- **Reviewer Agent**: Inspecting generated code on disk, running validation heuristics, and returning structured verdicts (`ReviewVerdict`).
- **Project Finalization**: Handing off verified deliverables to `manager_final` for the executive summary.

---

## Architecture in This Stage
```
                   ┌─> [ Researcher ] ─┐
START ──> [ Manager ]                  ├─> [ Developer ] <───┐ (changes requested)
                   └─> [  Planner   ] ─┘          │          │
                                                  ▼          │
                                            [ Reviewer ] ────┘
                                                  │ (approved OR max rounds)
                                                  ▼
                                          [ Manager Final ] ──> END
```

---

## How to Test

Run the CLI runner from your terminal:
```bash
python backend/cli.py "Build a pomodoro timer web page"
```

### Expected Output:
```
18:52:15 🚀 RUN STARTED — ID: run_20261014_185215_4a1f
       Prompt: Build a pomodoro timer web page

18:52:15 [ MANAGER  ] ⚡ Started work
...
18:52:25 [DEVELOPER ] 📝 Wrote index.html (1449 bytes)
18:52:25 [DEVELOPER ] 📝 Wrote styles.css (2253 bytes)
18:52:25 [DEVELOPER ] 📝 Wrote app.js (5702 bytes)
18:52:25 ➔ developer passed 'Code for review' to reviewer
18:52:25 [DEVELOPER ] ✓ Done — Developer completed task.
18:52:25 [ REVIEWER ] ⚡ Started work
18:52:25 [ REVIEWER ] ⋯ Evaluating code completeness & quality...
18:52:28 [ REVIEWER ] ⚖ Verdict (Round 1): APPROVED ✓
18:52:28 ➔ reviewer passed 'Approval verdict' to manager
18:52:28 [ REVIEWER ] ✓ Done — Review complete: approved
18:52:28 [ MANAGER  ] ⚡ Started work
18:52:28 [ MANAGER  ] ⋯ Finalizing project delivery...
18:52:31 [ MANAGER  ] ✓ Done — Final delivery ready

🏁 RUN COMPLETED
       Deliverables (3 files):
       • index.html
       • styles.css
       • app.js
```

All 5 agents are now collaborating in a resilient cyclical multi-agent graph!

Proceed to **Stage 6** to connect this graph to the FastAPI SSE server and launch the desktop Electron UI.
