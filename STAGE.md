# Stage 4: Developer Agent & Sandboxed File Tools

## Goal
Implement the real **Developer** agent that takes findings from the Researcher and architectural specs from the Planner, generates production-quality code, and writes real files (`index.html`, `styles.css`, `app.js`) to disk in a sandboxed `workspace/<run_id>/` folder.

---

## What We're Learning
- **Sandboxed Tool Calling (`make_file_tools`)**: Safe file operations restricted strictly to a dedicated run directory. Path traversal attempts (`../`) are blocked.
- **`emit("file_written")`**: Broadcasting file system mutation events with file path and byte counts so the frontend or CLI can update in real time.
- **Code Generation & Parsing**: Prompting Groq to output clean modular web applications and reliably extracting files.

---

## Architecture in This Stage
```
                   ┌─> [ Researcher ] ─┐
START ──> [ Manager ]                  ├─> [ Developer (Real Tools) ] ──> END
                   └─> [  Planner   ] ─┘          │
                                                  ▼
                                       workspace/<run_id>/
                                       ├── index.html
                                       ├── styles.css
                                       └── app.js
```

---

## How to Test

Run the CLI runner from your terminal:
```bash
python backend/cli.py "Build a pomodoro timer web page"
```

### Expected Output:
```
18:50:12 🚀 RUN STARTED — ID: run_20261014_185012_9b2e
       Prompt: Build a pomodoro timer web page

18:50:12 [ MANAGER  ] ⚡ Started work
...
18:50:17 [DEVELOPER ] ⚡ Started work
18:50:17 [DEVELOPER ] ⋯ Generating HTML, CSS, and JS code via LLM...
18:50:20 [DEVELOPER ] 📝 Wrote index.html (1420 bytes)
18:50:20 [DEVELOPER ] 📝 Wrote styles.css (1890 bytes)
18:50:20 [DEVELOPER ] 📝 Wrote app.js (2150 bytes)
18:50:20 ➔ developer passed 'Code for review' to reviewer
18:50:20 [DEVELOPER ] ✓ Done — Developer completed task.
```

Check your `workspace/run_.../` directory to see the real generated application files! Open `index.html` in your web browser to test it out.

Proceed to **Stage 5** to add the **Reviewer** and the iterative feedback loop.
