# Tensor Bots

Tensor Bots is an autonomous multi-agent engineering team (Manager, Researcher, Planner, Developer, Reviewer) built with **LangGraph** (Python 3.11+) and a modern **Electron / React** frontend. It demonstrates state graphs, parallel fan-out / fan-in, custom real-time event streaming, sandboxed file tools, and human-in-the-loop / review cycles.

---

## Workshop Setup

### macOS / Linux
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

### Configure Environment (.env)
Copy the template to create your local `.env`:
```bash
cp backend/.env.example backend/.env
```
Open `backend/.env` and optionally paste your `GROQ_API_KEY` (from https://console.groq.com/). If no key is set or `MOCK_LLM=1`, Tensor Bots runs in offline mock mode with simulated agent outputs.

---

## Workshop Stage Branches

During the workshop, follow along through these stages:

| Branch | Stage Title | Graph Architecture | Run Command |
|---|---|---|---|
| `stage-0-setup` | Setup & Environment | Single verification node | `python backend/hello_graph.py` |
| `stage-1-first-agent` | First Agent: Researcher | `START -> researcher -> END` | `python backend/cli.py "..."` |
| `stage-2-manager` | Manager Decomposition | `START -> manager -> researcher -> END` | `python backend/cli.py "..."` |
| `stage-3-parallel` | Parallel Fan-Out & Join | `manager -> [researcher, planner] -> developer -> END` | `python backend/cli.py "..."` |
| `stage-4-developer` | Real Developer & Tools | Same graph; writes code to `workspace/` | `python backend/cli.py "..."` |
| `stage-5-reviewer-loop` | Reviewer Loop & Wrap-up | Complete graph with revision loop | `python backend/cli.py "..."` |
| `stage-6-ui` | FastAPI SSE & Electron UI | Full system with SSE streaming server | `uvicorn app.main:app --port 8000 --app-dir backend` |

---

## Staying in Sync (For Attendees)

### Initial Clone (GitHub Desktop)
1. Open GitHub Desktop and select **File > Clone repository...**
2. Select the **URL** tab and paste:
   ```text
   https://github.com/md-Yusha/tensor-bots.git
   ```
3. Choose your local folder and clone. **Do NOT fork the repository.**

### Catching Up After Each Stage
At the end of each stage, the instructor merges new code into `main`. To catch up:
1. In GitHub Desktop, open the **Changes** tab on the left.
2. Right-click the changed files list and choose **Discard all changes** (never click Commit).
3. Click **Fetch origin** in the top bar.
4. Click **Pull origin**.

> **Note:** `.env` and `venv/` are gitignored and safe from being overwritten or discarded.

### CLI Alternative (macOS / Linux)
```bash
git restore . && git clean -fd -e .env -e venv && git pull
```

### Last-Resort Stage ZIP
If git gets stuck, download the standalone snapshot for any stage:
```text
https://github.com/md-Yusha/tensor-bots/archive/refs/heads/<branch>.zip
```

---

## Top 5 Troubleshooting Tips

1. **Virtual environment not active:**
   If imports fail with `ModuleNotFoundError`, make sure your venv is activated (`source venv/bin/activate` or `.\venv\Scripts\Activate.ps1`).
2. **API key not loaded (running in MOCK mode):**
   If you see `[WARN] No Groq API key found, running in MOCK mode`, check that your key is pasted in `backend/.env` without extra quotes or spaces, and `MOCK_LLM=0`.
3. **Model not found:**
   If you receive a model not found error, ensure `GROQ_MODEL=openai/gpt-oss-120b` in `backend/.env`.
4. **Port 8000 in use:**
   If `uvicorn` fails to bind, find and kill the hanging process: `lsof -i :8000` (macOS/Linux) or `netstat -ano | findstr :8000` (Windows), or pass `--port 8001`.
5. **Git pull blocked by local changes:**
   Discard uncommitted edits in GitHub Desktop or run `git restore . && git clean -fd -e .env -e venv` before pulling.
