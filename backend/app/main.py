"""
LangGraph Idea: Server-Sent Events (SSE) Streaming API
------------------------------------------------------
To power modern interactive dashboards, LangGraph's generator output from
`graph.stream(stream_mode="custom")` is mapped directly to a Server-Sent Events (SSE)
stream via FastAPI's `StreamingResponse`. The browser and Electron client
receive fine-grained JSON events in real-time as each agent updates its state.
# TEACH: SSE translates LangGraph custom events into standard web streams.
"""

import json
import time
import uuid
import sys
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, PlainTextResponse, JSONResponse
from pydantic import BaseModel

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.config import (
    MOCK_LLM,
    GEMINI_MODEL,
    LLM_PROVIDER,
    GROQ_MODEL,
    WORKSPACE_DIR,
)
from app.events import emit
from app.graph import graph
from app.tools import _safe_resolve

app = FastAPI(title="Tensor Bots API", version="1.0.0")

# Enable CORS for Vite dev server, Electron (file:// or null origin), and local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "file://",
        "null",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    prompt: str


@app.get("/api/health")
def health():
    """Health check endpoint indicating model provider and mock status."""
    active_model = GROQ_MODEL if LLM_PROVIDER == "groq" else GEMINI_MODEL
    return {
        "ok": True,
        "mock": MOCK_LLM,
        "model": active_model,
        "provider": LLM_PROVIDER,
    }


@app.post("/api/run")
def run_endpoint(req: RunRequest):
    """
    Executes the multi-agent graph for the given user prompt and streams
    SSE events as `data: <json>\n\n`.
    """
    prompt = req.prompt.strip() or "Build a pomodoro timer web page"
    run_id = f"run_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
    run_dir = WORKSPACE_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    def event_generator():
        # Emit initial run_started event
        start_payload = {
            "type": "run_started",
            "ts": time.time(),
            "run_id": run_id,
            "prompt": prompt,
        }
        yield f"data: {json.dumps(start_payload)}\n\n"

        initial_state = {
            "run_id": run_id,
            "user_prompt": prompt,
            "iteration": 0,
            "files": [],
        }

        try:
            # Stream custom events produced by get_stream_writer()
            for event in graph.stream(initial_state, stream_mode="custom"):
                if isinstance(event, dict):
                    yield f"data: {json.dumps(event)}\n\n"
        except Exception as exc:
            err_payload = {
                "type": "run_error",
                "ts": time.time(),
                "message": str(exc),
            }
            yield f"data: {json.dumps(err_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/files/{run_id}")
def list_run_files(run_id: str):
    """List all created files inside workspace/<run_id>/ with sizes."""
    try:
        run_dir = _safe_resolve(WORKSPACE_DIR, run_id)
        if not run_dir.exists():
            return {"files": []}
        
        file_list = []
        for item in sorted(run_dir.rglob("*")):
            if item.is_file():
                rel = str(item.relative_to(run_dir))
                file_list.append({
                    "path": rel,
                    "bytes": item.stat().st_size,
                })
        return {"files": file_list}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/files/{run_id}/{file_path:path}")
def get_file_content(run_id: str, file_path: str):
    """Retrieve text content of a specific file inside workspace/<run_id>/."""
    try:
        run_dir = _safe_resolve(WORKSPACE_DIR, run_id)
        target = _safe_resolve(run_dir, file_path)
        if not target.exists() or not target.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        return PlainTextResponse(target.read_text(encoding="utf-8"))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
