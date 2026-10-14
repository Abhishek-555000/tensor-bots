# Stage 6: FastAPI SSE & Desktop Electron UI

## Goal
Connect your 5-agent LangGraph system to a **FastAPI Server-Sent Events (SSE)** backend and launch the custom **Electron + React desktop UI** with real-time particle animations, robot state avatars, and interactive code preview.

---

## What We're Learning
- **Server-Sent Events (`StreamingResponse`)**: Streaming LangGraph events live from the Python backend to the frontend over HTTP using SSE format (`data: {json}\n\n`).
- **Zustand State Reduction**: Transforming raw graph lifecycle events (`agent_status`, `handoff`, `file_written`, `review_verdict`) into reactive UI state.
- **Custom Constellation & Particle Animations**: Visualizing agent collaboration, parallel fan-out, and the review loop.
- **Electron Integration**: Desktop application container with native window controls and file system access.

---

## Architecture
```
┌────────────────────────────────────────────────────────┐
│                   Electron Desktop App                 │
│   (Constellation, Avatars, Particles, Code Viewer)     │
└───────────────────────────▲────────────────────────────┘
                            │ SSE Stream (POST /api/run)
┌───────────────────────────┴────────────────────────────┐
│                    FastAPI Backend                     │
│                (app/main.py: /api/run)                 │
└───────────────────────────▲────────────────────────────┘
                            │ graph.stream(stream_mode="custom")
┌───────────────────────────┴────────────────────────────┐
│                  5-Agent LangGraph System              │
│       Manager ➔ [Researcher | Planner] ➔ Developer     │
│                 Reviewer ↺ Developer ➔ Manager Final   │
└────────────────────────────────────────────────────────┘
```

---

## How to Run

### 1. Start the Backend API
In your first terminal:
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```
Verify the backend is healthy:
```bash
curl http://localhost:8000/api/health
```
*(Should return `{"status": "ok", "mock_llm": false, "provider": "groq", ...}`)*

---

### 2. Launch the Electron Desktop App
In your second terminal:
```bash
cd frontend
npm install
npm run dev
```

Type a prompt into the floating bar (e.g., *"Build a pomodoro timer web page"*), hit **Enter**, and watch the Tensor Bots crew collaborate in real-time!
