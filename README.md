# Tensor Bots — Multi-Agent AI Workshop Reference Project

Tensor Bots is an autonomous multi-agent engineering team (Manager, Researcher, Planner, Developer, Reviewer) orchestrated with **LangGraph** and presented with a modern **React + Electron** animated constellation UI.

## 🚀 Quickstart

```bash
# 1. Backend Setup (Python 3.11+)
python3 -m venv venv && source venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env    # Add your GEMINI_API_KEY / GOOGLE_API_KEY

# 2. Verify Connectivity (Stage 0)
python backend/hello_graph.py

# 3. Run Multi-Agent Crew in CLI (Stages 1–5)
python backend/cli.py "Build a pomodoro timer web page"

# 4. Start Backend API Server
uvicorn app.main:app --port 8000 --app-dir backend

# 5. Launch Frontend Constellation (Electron / Web)
cd frontend && npm install && npm run dev
```

> **Offline Mock Mode:** Run with `MOCK_LLM=1` in your `.env` to execute the full graph, tools, and UI offline with realistic simulated outputs!
