# Tensor Bots — Build Prompt

> **How to use this file:** paste it (whole) into Claude Code or any coding agent, or hand it to a team member, to build the complete reference project *before* the workshop. It is self-contained. The companion file `tensor-bots-project-plan.md` explains the "why" and the run of show.

---

## 1. Role & goal

You are a senior engineer building **Tensor Bots**, the reference project for the Tensor Club *Multi Agent AI-Workshop* (MVJCE, 15 Oct 2026).

Tensor Bots is a desktop app where a user types one request into a chat box. A **Project Manager** agent breaks it down and dispatches it to four teammates (**Researcher, Planner/Designer, Developer, Reviewer**). They work, hand off to each other, wait on each other, and loop until the Reviewer approves. The user watches the *flow* as a clean animated graph, not a wall of text.

The workshop **teaches the backend** (Python + LangGraph). The **frontend is distributed as finished code** that participants copy in, so it must be polished, but it is not taught.

Two outputs are required:
1. A **complete, working project** (`main`).
2. A **teachable version**: a `starter` branch with TODO stubs and `stage-N-solution` tags (see §9).

## 2. Hard constraints

- Backend: **Python 3.11+, LangGraph, LangChain, FastAPI**, LLM = **Groq Cloud API** via `langchain-groq`. Read `GROQ_API_KEY` from `.env`; model name from `GROQ_MODEL` (default `openai/gpt-oss-120b`, must be changeable without code edits).
- Frontend: **React + Vite + TypeScript, Tailwind CSS, Electron, Framer Motion, zustand**. No React Flow (custom SVG for full control of the look).
- Audience: intermediate Python students on their own laptops (Windows/macOS/Linux). Keep every backend file **short, readable, heavily commented**. Prefer clarity over cleverness. No unnecessary abstractions, no class hierarchies.
- **Pin exact versions** of every dependency in `requirements.txt` / `package.json` after you have tested them together. Verify current LangGraph / `langchain-groq` APIs against their docs before using them (import paths change between versions).
- Researcher is **LLM-only (no web search)** to keep setup simple.
- Developer **writes real files** to disk using tools, inside a sandboxed folder. No code execution.
- Must work **offline-capable for the UI** (bundle fonts locally; no CDN at runtime).
- A **`MOCK_LLM=1` mode** must exist: every agent returns canned, realistic output (with short delays) so the full graph, events and UI work with no API key / no internet. This is the workshop safety net.

## 3. Repo layout

```
tensor-bots/
├─ README.md                 # 10-line quickstart
├─ backend/
│  ├─ requirements.txt
│  ├─ .env.example           # GROQ_API_KEY=, GROQ_MODEL=, MOCK_LLM=0, MAX_REVIEW_ROUNDS=2
│  ├─ hello_graph.py         # stage 0: proves key + LangGraph work
│  ├─ cli.py                 # runs the graph, pretty-prints events (used in stages 1–5)
│  └─ app/
│     ├─ main.py             # FastAPI: /api/health, /api/run (SSE), /api/files
│     ├─ config.py           # env loading, constants
│     ├─ llm.py              # get_llm(); returns a mock when MOCK_LLM=1
│     ├─ state.py            # TensorState (TypedDict) + pydantic schemas
│     ├─ events.py           # emit() helper + @agent_node decorator
│     ├─ tools.py            # make_file_tools(root) -> read_file, write_file, list_files
│     ├─ graph.py            # builds + compiles the StateGraph
│     └─ agents/
│        ├─ manager.py       # manager_plan, manager_final
│        ├─ researcher.py
│        ├─ planner.py
│        ├─ developer.py
│        └─ reviewer.py
├─ workspace/                # gitignored; one subfolder per run (workspace/<run_id>/)
└─ frontend/                 # Electron + React app (see §7)
```

## 4. Backend spec

### 4.1 Graph topology

```
START → manager ─┬→ researcher ─┐
                 └→ planner ────┴→ developer → reviewer ─┬─(approved or rounds ≥ MAX)→ manager_final → END
                                      ▲                   │
                                      └──── (changes requested) ┘
```

- `manager` produces a structured **brief** for each of the four agents (pydantic model, via `with_structured_output`).
- `researcher` and `planner` run **in parallel** (fan-out), and `developer` **waits for both** (join: `add_edge(["researcher","planner"], "developer")`).
- `reviewer` returns a structured `Verdict {approved: bool, issues: list[str], summary: str}`. A conditional edge routes to `developer` (revise) or `manager_final`. Cap rounds at `MAX_REVIEW_ROUNDS` (default 2) so it can never loop forever.
- `manager_final` writes the user-facing summary.
- Nodes named `manager` and `manager_final` both appear as the **same** "manager" agent in events/UI.

### 4.2 State (`state.py`)

`TensorState` (TypedDict, `total=False`): `run_id`, `user_prompt`, `briefs`, `research`, `plan`, `files` (list[str]), `review` (dict), `iteration` (int), `final_summary`. Parallel branches write **different keys**, so no reducers are needed (note this in a comment, as it is a teaching point).

### 4.3 Agents

| Agent | Reads | Writes | Notes |
|---|---|---|---|
| manager | `user_prompt` | `briefs` | Structured output. Briefs are 1–3 sentences each. |
| researcher | `briefs.researcher` | `research` | Short markdown: key facts, constraints, risks, recommended approach. LLM only. |
| planner | `briefs.planner` | `plan` | Short markdown: file list (≤ 4 files), structure, UI/UX decisions. |
| developer | `research`, `plan`, `review` (if revising) | `files`, `iteration` | ReAct-style agent with `write_file`/`read_file`/`list_files`. Max 4 files, small. On revision rounds it must read the Reviewer's `issues` and fix them. |
| reviewer | `plan`, files on disk | `review` | Uses `read_file`/`list_files`. Checks files exist, match the plan, obvious bugs. Strict but fair. |
| manager_final | everything | `final_summary` | 3–5 line summary + list of files. |

Prompts live as module-level constants at the top of each agent file (easy to find and tweak live). Draft prompts are in the plan doc.

### 4.4 Tools (`tools.py`)

`make_file_tools(root: Path)` returns LangChain `@tool` functions **bound by closure to `workspace/<run_id>/`**. Reject absolute paths and `..` (resolve and verify the path stays inside `root`). `write_file` creates parent folders and emits a `file_written` event.

### 4.5 Events (`events.py`)

Nodes emit events via `from langgraph.config import get_stream_writer`. Provide:
- `emit(type, **data)`
- `@agent_node("researcher")` decorator that emits `agent_started` / `agent_done` / `agent_error` around the node.

Run the graph with `graph.stream(initial_state, stream_mode="custom")` in a **sync** generator (works on Python 3.11+).

**Event schema** (each is one JSON object with a `type` and a `ts` timestamp):

| type | fields | when |
|---|---|---|
| `run_started` | `run_id`, `prompt` | start |
| `agent_started` | `agent` | node begins |
| `agent_status` | `agent`, `text` (≤ 6 words, e.g. "Reading the plan") | during work |
| `agent_waiting` | `agent`, `on` (list of agents) | manager emits this for developer (on researcher, planner) and reviewer (on developer) right after dispatch |
| `handoff` | `from`, `to`, `label` (≤ 3 words) | whenever work moves between agents |
| `agent_output` | `agent`, `text` (markdown) | when an agent has a full result for the detail panel |
| `file_written` | `agent`, `path`, `bytes` | each write_file |
| `review_verdict` | `approved`, `issues`, `iteration` | reviewer done |
| `agent_done` | `agent`, `summary` (one line) | node ends |
| `run_finished` | `summary`, `files` | end |
| `run_error` | `message` | any failure (never crash silently) |

Handoffs to emit: manager→researcher, manager→planner, researcher→developer, planner→developer, developer→reviewer, reviewer→developer (label "changes"), reviewer→manager (label "approved"), manager→user is not an edge (use `run_finished`).

### 4.6 API (`main.py`)

- `GET /api/health` → `{ok: true, mock: bool, model: str}`
- `POST /api/run` body `{prompt: str}` → **SSE** stream (`text/event-stream`, `data: <json>\n\n`), ends after `run_finished` or `run_error`. Create `workspace/<run_id>/` per run.
- `GET /api/files/{run_id}` → list of files; `GET /api/files/{run_id}/{path:path}` → file text (path-sandboxed).
- CORS: allow `http://localhost:5173` and `file://`/`null` origin for Electron.

### 4.7 CLI (`cli.py`)

`python cli.py "build a pomodoro timer web page"` runs the graph and prints events in a readable one-line-each format. Participants use this in stages 1–5 before the UI is connected.

## 5. Developer-agent guardrails

- ≤ 4 files, each < 150 lines; plain HTML/CSS/JS or a single Python script. Tell the model this in the prompt.
- If Groq returns malformed tool calls or an empty response, retry once, then emit `run_error` with a clear message.
- Wrap LLM calls in a small retry (2 attempts, short backoff) to survive rate-limit blips. Surface "rate limited, retrying" as an `agent_status`.

## 6. Mock mode

When `MOCK_LLM=1`, `llm.py` and the agents return deterministic canned content (a small static HTML page as the "built" project), with 0.8–2 s delays and the same events as the real run. Parallel agents must still overlap in time. The UI must be indistinguishable apart from a tiny "mock" tag near the health dot.

## 7. Frontend spec (this is the showpiece)

**Vibe:** minimalist, quiet, confident, like Claude Code's terminal UI translated into a graphical app, themed on the Tensor poster (deep violet/black, soft pink + violet glow, thin lines, isometric-platform feel). Almost no text on screen. Nothing decorative that doesn't carry information.

### 7.1 Theme tokens (Tailwind config)

- Background `#07040F` with a very faint radial violet glow center and subtle dot/circuit grain.
- Surface `#120A24`, border `rgba(167,139,250,0.18)`.
- Primary violet `#A78BFA`, deep violet `#7C3AED`, accent pink `#F472B6`, text `#E4E0F0` / muted `#8B84A3`, error `#F87171`.
- Fonts (bundled via `@fontsource`): **Inter** for UI, **JetBrains Mono** for tiny labels/status.
- Radius 12–16 px, 1 px borders, glow via soft `box-shadow`, never heavy gradients.

### 7.2 Layout (single window, no sidebars at rest)

- **Center stage:** the agent constellation (SVG), echoing the poster: Project Manager in the middle; Researcher top-left, Planner/Designer bottom-left, Developer top-right, Reviewer bottom-right; a faint dotted orbit ring connecting them.
- **Bottom:** one floating input bar (single line, placeholder "Ask the Project Manager…", Enter to send, subtle send glyph). Idle state shows a short centered title "Tensor Bots" and 3 tiny example-prompt chips.
- **After submit:** the user's prompt collapses into a small pill at the top center; the input bar fades to a quiet "Running…" / stop control.
- **Top-right corner:** a 6 px health dot (green = backend ok, red = down) and a tiny `mock` tag when applicable.
- **Frameless-look window** (hidden title bar with a draggable region, native window controls via `titleBarOverlay` on Windows / `hiddenInset` on macOS).

### 7.3 Agents

Each agent is a small **SVG robot avatar** (rounded-square head, two eyes, antenna, a distinct chest glyph: search, sparkle, `</>`, check, branch) sitting on an **isometric diamond platform**, in the poster style, with the role name underneath in small caps.

States (driven by events, visually distinct without text):
- **idle**: dim, slow eye blink.
- **waiting**: dashed ring around the platform, eyes half-closed, a tiny "waiting on Researcher" caption in muted mono.
- **working**: platform glows (agent accent color), eyes scan left-right, a thin orbiting ring, `agent_status` text (≤ 6 words) fades in under the name.
- **done**: steady soft glow, a small check badge.
- **error**: red tint, shake once.
Transitions ~250–400 ms, eased. Respect `prefers-reduced-motion`.

### 7.4 Flow animations

- Edges are thin dotted curves between platforms. On a `handoff` event, a glowing **particle** travels along the edge from → to (≈ 700 ms) leaving a brief trail, and the target's ring "catches" it. The edge label (≤ 3 words) appears briefly mid-travel.
- Parallel fan-out (manager → researcher & planner) fires both particles together. The join into Developer should visibly **gather** (two particles arriving).
- The reviewer→developer "changes" loop uses the pink accent; "approved" uses violet and ends with a gentle pulse through the manager.
- Keep ≤ 3 simultaneous particles for performance.

### 7.5 Detail panel (hover + click)

- **Hover** an agent: a small floating card (≈ 240 px) with state, current one-line status, and files written count.
- **Click**: a slim right slide-over panel (≈ 380 px, glass/blur surface). Contents, in order, all compact:
  1. Header: avatar, name, state chip.
  2. **Brief** (the task this agent was given), collapsed to 3 lines with expand.
  3. **Output** (`agent_output`, rendered markdown via `react-markdown`).
  4. **Files** (for Developer/Reviewer): list with sizes; clicking opens a read-only code view (monospace, simple, no heavy editor library).
  5. For Reviewer: verdict, and issues as a short list per round.
- `Esc` or clicking outside closes it. Live-updates while the agent works. Works for completed runs too.

### 7.6 Finish state

On `run_finished`: a compact bottom card slides up: "Done · N files" with the Manager's 3–5 line summary and a file list; a button "Open folder" (Electron `shell.showItemInFolder`) and "New run". No confetti.

### 7.7 Frontend internals

- `useRunStore` (zustand) reduces the SSE events into: `agents{state,status,brief,output,files[]}`, `particles[]`, `verdicts[]`, `runState`, `summary`.
- `useEventStream(prompt)` uses `fetch` + `ReadableStream` to read the POST SSE (EventSource can't POST). Parse `data:` lines robustly (chunks can split mid-line).
- Also include a **replay mode**: load a saved JSON of a previous run's events and replay them with timing. This lets us demo the UI without any backend.
- Electron: `main.ts`, `preload.ts` (contextIsolation on, expose only `openFolder(path)`), dev script that runs Vite and Electron together. Backend URL via `VITE_API_URL` (default `http://localhost:8000`).
- Single `npm install && npm run dev` must work for participants. Include a **production build check** (`npm run build`).

## 8. Teaching comments

At the top of each backend file, add a 3–5 line comment explaining the **one LangGraph idea** it demonstrates (state, nodes, edges, fan-out/join, conditional edges, tools, streaming). Mark spots speakers will live-explain with `# TEACH:`.

## 9. Branches & checkpoints

- `main`: finished project.
- `starter`: complete frontend + backend skeleton where each agent/graph piece is a stub with `# TODO(stage-N)` and a clear docstring of what to implement.
- Tags `stage-0-solution` … `stage-6-solution`: the backend after each stage, each **runnable** on its own:

| Stage | Participants build | Run with |
|---|---|---|
| 0 | env, `.env`, `hello_graph.py` (one Groq call inside a 1-node graph) | `python hello_graph.py` |
| 1 | `TensorState`, first real node, `cli.py` wiring | `python cli.py "..."` |
| 2 | Manager: structured output → briefs, `add_edge` | cli |
| 3 | Researcher + Planner in parallel, join into a developer stub | cli |
| 4 | File tools + real Developer | cli (check `workspace/`) |
| 5 | Reviewer, conditional edge, round cap | cli |
| 6 | `emit()` events, `@agent_node`, FastAPI SSE → connect the UI | Electron app |

## 10. Quality bar / Definition of done

- [ ] Fresh clone → follow README → working run on a clean Windows and a clean macOS/Linux machine.
- [ ] Full run in real Groq mode completes in **under ~2 minutes** for the demo prompts below, and in mock mode in ~20 s.
- [ ] Review loop demonstrably triggers at least once on some prompts and terminates by the cap.
- [ ] No unhandled exceptions: all failures become `run_error` with a human message.
- [ ] Animations at a smooth 60 fps on a mid-range laptop; no layout jumps.
- [ ] Every `stage-N-solution` tag runs. `starter` runs up to the first TODO with a clear message.
- [ ] `requirements.txt` and `package-lock.json` are pinned and committed.

**Demo prompts to test with:** "A pomodoro timer web page", "A Python CLI that renames files by date", "A personal landing page with a dark theme", "A tip calculator in HTML/JS".

## 11. Out of scope

Auth, databases, deployment, web search, code execution, multi-user, packaging installers.

## 12. Order of work

1. Backend skeleton + mock mode + `cli.py` (get a full mock run printing events).
2. Real Groq agents, tools, review loop; tune prompts until the demo prompts succeed reliably.
3. FastAPI SSE; save one real run's events as `replay.json`.
4. Frontend with replay mode first (no backend needed), then live SSE.
5. Cut `starter` and the `stage-N-solution` tags; test each from a clean checkout.
6. README + final cross-platform test.

Report back with: a summary of what was built, anything you could not verify (versions, APIs), and the exact commands to run each stage.
