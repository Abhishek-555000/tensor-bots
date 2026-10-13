import json
import time
import uuid
import sys
import hashlib
import logging
import shutil
import threading
from pathlib import Path
from typing import Any

import mimetypes
import subprocess
import os
import platform
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    StreamingResponse,
    PlainTextResponse,
    JSONResponse,
    FileResponse,
    RedirectResponse,
    HTMLResponse,
)
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
from app.graph import graph
from app.tools import _safe_resolve

app = FastAPI(title="Tensor Bots API", version="1.0.0")
logger = logging.getLogger(__name__)

_RUN_CACHE_DIR = BASE_DIR / ".cache" / "prompt-runs"
_RUN_CACHE_VERSION = "2026-10-prompt-isolation-v3"
_run_cache_locks: dict[str, threading.Lock] = {}
_run_cache_locks_guard = threading.Lock()


def _cache_key(prompt: str) -> str:
    """Return a stable key for this exact prompt and active generation configuration."""
    cache_identity = {
        "version": _RUN_CACHE_VERSION,
        "prompt": prompt,
        "mock": MOCK_LLM,
        "provider": LLM_PROVIDER,
        "model": GROQ_MODEL if LLM_PROVIDER == "groq" else GEMINI_MODEL,
    }
    encoded_identity = json.dumps(cache_identity, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded_identity).hexdigest()


def _cache_lock(key: str) -> threading.Lock:
    """Serialize same-prompt builds so simultaneous requests share one generated result."""
    with _run_cache_locks_guard:
        return _run_cache_locks.setdefault(key, threading.Lock())


def _load_cached_run(key: str, run_dir: Path, prompt: str) -> list[dict[str, Any]] | None:
    """Copy a completed cached project into this run and return its event history."""
    cache_dir = _RUN_CACHE_DIR / key
    files_dir = cache_dir / "files"
    events_path = cache_dir / "events.json"
    if not files_dir.is_dir() or not events_path.is_file():
        return None

    try:
        cached_run = json.loads(events_path.read_text(encoding="utf-8"))
        if (
            not isinstance(cached_run, dict)
            or cached_run.get("prompt") != prompt
            or not isinstance(cached_run.get("events"), list)
        ):
            logger.warning("Ignoring mismatched generated-project cache entry %s", key)
            return None
        events = cached_run["events"]
        if not all(isinstance(event, dict) for event in events):
            logger.warning("Ignoring malformed generated-project cache entry %s", key)
            return None
        if not any(
            event.get("type") == "run_finished"
            for event in events
        ):
            logger.warning("Ignoring incomplete generated-project cache entry %s", key)
            return None
        shutil.copytree(files_dir, run_dir, dirs_exist_ok=True)
        return events
    except (OSError, ValueError, TypeError) as exc:
        logger.warning("Could not read generated-project cache entry %s: %s", key, exc)
        return None


def _save_cached_run(key: str, run_dir: Path, prompt: str, events: list[dict[str, Any]]) -> None:
    """Persist a successful run's exact files and emitted UI events."""
    cache_dir = _RUN_CACHE_DIR / key
    if cache_dir.exists():
        return

    _RUN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    temp_dir = _RUN_CACHE_DIR / f".{key}.{uuid.uuid4().hex}.tmp"
    try:
        temp_dir.mkdir()
        shutil.copytree(run_dir, temp_dir / "files")
        (temp_dir / "events.json").write_text(
            json.dumps({"prompt": prompt, "events": events}, ensure_ascii=False),
            encoding="utf-8",
        )
        temp_dir.replace(cache_dir)
    except OSError:
        logger.exception("Could not save generated-project cache entry %s", key)
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

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

        key = _cache_key(prompt)
        with _cache_lock(key):
            cached_events = _load_cached_run(key, run_dir, prompt)
            if cached_events is not None:
                for cached_event in cached_events:
                    event = {**cached_event, "ts": time.time()}
                    yield f"data: {json.dumps(event)}\n\n"
                return

            initial_state = {
                "run_id": run_id,
                "user_prompt": prompt,
                "iteration": 0,
                "files": [],
            }
            captured_events: list[dict[str, Any]] = []

            try:
                # Stream custom events produced by get_stream_writer()
                for event in graph.stream(initial_state, stream_mode="custom"):
                    if isinstance(event, dict):
                        captured_events.append(event)
                        yield f"data: {json.dumps(event)}\n\n"

                if any(event.get("type") == "run_finished" for event in captured_events):
                    _save_cached_run(key, run_dir, prompt, captured_events)
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


@app.post("/api/open-folder/{run_id}")
def open_workspace_folder(run_id: str):
    """Opens workspace/<run_id> folder in host operating system file explorer."""
    try:
        run_dir = _safe_resolve(WORKSPACE_DIR, run_id)
        if not run_dir.exists():
            run_dir.mkdir(parents=True, exist_ok=True)

        system = platform.system()
        if system == "Windows":
            os.startfile(str(run_dir))
        elif system == "Darwin":
            subprocess.Popen(["open", str(run_dir)])
        else:
            subprocess.Popen(["xdg-open", str(run_dir)])
        return {"ok": True, "path": str(run_dir)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


def _generate_python_terminal_html(run_id: str, script_name: str) -> str:
    """Renders a sleek interactive console for executing Python scripts."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Python Runner - {script_name}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "JetBrains Mono", monospace; }}
    body {{ background: #07040F; color: #E4E0F0; padding: 20px; min-height: 100vh; display: flex; flex-direction: column; }}
    .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; padding-bottom: 12px; border-bottom: 1px solid rgba(167, 139, 250, 0.2); flex-wrap: gap: 8px; }}
    .title {{ font-size: 14px; font-weight: 700; color: #A78BFA; display: flex; align-items: center; gap: 8px; }}
    .dot {{ width: 8px; height: 8px; border-radius: 50%; background: #10B981; box-shadow: 0 0 8px #10B981; }}
    .actions {{ display: flex; align-items: center; gap: 8px; }}
    .btn {{ background: #7C3AED; color: #FFF; border: none; padding: 7px 14px; border-radius: 8px; font-size: 11px; font-weight: 600; cursor: pointer; transition: all 0.2s; display: inline-flex; align-items: center; gap: 6px; }}
    .btn:hover {{ background: #6D28D9; }}
    .btn-secondary {{ background: rgba(255, 255, 255, 0.08); color: #C4B5FD; }}
    .btn-secondary:hover {{ background: rgba(255, 255, 255, 0.15); }}
    .cmd-bar {{ display: flex; align-items: center; gap: 8px; margin-bottom: 12px; background: #0F0822; padding: 8px 12px; border-radius: 10px; border: 1px solid rgba(167, 139, 250, 0.15); font-size: 12px; }}
    .cmd-prompt {{ color: #EC4899; font-weight: 600; }}
    .cmd-input {{ flex: 1; background: transparent; border: none; color: #E4E0F0; font-family: inherit; font-size: 12px; outline: none; }}
    .terminal {{ flex: 1; background: #0B0617; border: 1px solid rgba(167, 139, 250, 0.18); border-radius: 12px; padding: 18px; overflow-y: auto; font-size: 12.5px; line-height: 1.6; box-shadow: inset 0 2px 12px rgba(0,0,0,0.6); }}
    .stdout {{ color: #E4E0F0; white-space: pre-wrap; }}
    .stderr {{ color: #F87171; white-space: pre-wrap; }}
    .meta-bar {{ display: flex; justify-content: space-between; align-items: center; margin-top: 10px; font-size: 11px; color: #8B84A3; }}
    .badge {{ display: inline-flex; padding: 2px 8px; border-radius: 9999px; font-size: 10px; font-weight: 600; }}
    .badge-success {{ background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .badge-error {{ background: rgba(239, 68, 68, 0.15); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.3); }}
  </style>
</head>
<body>
  <div class="header">
    <div class="title"><span class="dot"></span> Python Console: {script_name}</div>
    <div class="actions">
      <button class="btn btn-secondary" onclick="copyOutput()" id="copyBtn">📋 Copy</button>
      <button class="btn btn-secondary" onclick="clearOutput()">🧹 Clear</button>
      <button class="btn" onclick="runScript()">▶ Run</button>
    </div>
  </div>
  <div class="cmd-bar">
    <span class="cmd-prompt">$ python {script_name}</span>
    <input type="text" id="cliArgs" class="cmd-input" placeholder="optional CLI arguments (press Enter to run)" onkeydown="if(event.key==='Enter') runScript()" />
  </div>
  <div class="terminal" id="terminal">
    <div id="output" class="stdout">Executing script...</div>
  </div>
  <div class="meta-bar">
    <span id="status">Starting runtime...</span>
    <span id="badge" class="badge"></span>
  </div>
  <script>
    async function runScript() {{
      const out = document.getElementById("output");
      const stat = document.getElementById("status");
      const badge = document.getElementById("badge");
      out.className = "stdout";
      out.textContent = "Executing script in workspace/{run_id}...";
      stat.textContent = "Running...";
      badge.textContent = "";
      badge.className = "badge";
      try {{
        const res = await fetch("/api/execute/{run_id}?script={script_name}");
        const data = await res.json();
        if (data.ok) {{
          out.className = "stdout";
          out.textContent = data.stdout || "[Script completed with no standard output]";
          stat.textContent = `Completed in ${{data.duration}}s (exit code ${{data.exit_code}})`;
          badge.textContent = "EXIT 0";
          badge.className = "badge badge-success";
        }} else {{
          out.className = "stderr";
          out.textContent = data.stderr || data.error || "Script failed.";
          stat.textContent = `Exited in ${{data.duration}}s (exit code ${{data.exit_code}})`;
          badge.textContent = `ERROR ${{data.exit_code}}`;
          badge.className = "badge badge-error";
        }}
      }} catch (err) {{
        out.className = "stderr";
        out.textContent = "Execution request failed: " + err.message;
        stat.textContent = "Failed";
        badge.textContent = "NETWORK ERROR";
        badge.className = "badge badge-error";
      }}
    }}
    function clearOutput() {{
      document.getElementById("output").textContent = "";
      document.getElementById("status").textContent = "Cleared";
      document.getElementById("badge").textContent = "";
    }}
    function copyOutput() {{
      const text = document.getElementById("output").textContent;
      navigator.clipboard.writeText(text);
      const btn = document.getElementById("copyBtn");
      btn.textContent = "✓ Copied";
      setTimeout(() => btn.textContent = "📋 Copy", 2000);
    }}
    runScript();
  </script>
</body>
</html>"""


def _generate_file_index_html(run_id: str, run_dir: Path) -> str:
    """Renders a file browser if no runnable entrypoint is detected."""
    files = sorted([p.name for p in run_dir.iterdir() if p.is_file()])
    links = "".join(f'<li><a href="/api/preview/{run_id}/{f}">{f}</a></li>' for f in files)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Workspace Files - {run_id}</title>
  <style>
    body {{ background: #07040F; color: #E4E0F0; font-family: sans-serif; padding: 32px; }}
    h1 {{ color: #A78BFA; font-size: 20px; margin-bottom: 16px; }}
    ul {{ list-style: none; padding: 0; }}
    li {{ margin: 8px 0; }}
    a {{ color: #F472B6; text-decoration: none; font-family: monospace; font-size: 14px; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <h1>Workspace Deliverables: {run_id}</h1>
  <ul>{links or "<li>No files found.</li>"}</ul>
</body>
</html>"""


@app.get("/api/preview/{run_id}")
def preview_redirect(run_id: str):
    """Ensure trailing slash so browser resolves relative assets (styles.css, app.js) correctly."""
    return RedirectResponse(url=f"/api/preview/{run_id}/", status_code=307)


@app.get("/api/preview/{run_id}/")
def preview_root(run_id: str):
    """
    Primary project launcher endpoint.
    Serves index.html, runs Python scripts in an interactive console,
    or lists generated deliverables.
    """
    try:
        run_dir = _safe_resolve(WORKSPACE_DIR, run_id)
        if not run_dir.exists() or not run_dir.is_dir():
            raise HTTPException(status_code=404, detail=f"Run directory '{run_id}' not found.")

        # 1. Root index.html
        index_file = run_dir / "index.html"
        if index_file.exists() and index_file.is_file():
            content = index_file.read_text(encoding="utf-8", errors="ignore")
            from app.agents.developer import is_html_broken, _generate_template_for_prompt
            if is_html_broken(content):
                # Detect prompt intent or keywords from file or run_id
                prompt_hint = run_id
                c_low = content.lower()
                if any(k in c_low or k in run_id.lower() for k in ("snake", "arcade", "game")):
                    prompt_hint = "snake game"
                elif any(k in c_low or k in run_id.lower() for k in ("calc", "calculator")):
                    prompt_hint = "calculator"
                elif any(k in c_low or k in run_id.lower() for k in ("tic", "tac", "toe")):
                    prompt_hint = "tic tac toe"
                elif any(k in c_low or k in run_id.lower() for k in ("todo", "task", "note")):
                    prompt_hint = "todo app"
                
                template = _generate_template_for_prompt(prompt_hint)
                try:
                    index_file.write_text(template["html"], encoding="utf-8")
                    css_file = run_dir / "styles.css"
                    if not css_file.exists() or len(css_file.read_text(encoding="utf-8", errors="ignore")) < 50:
                        css_file.write_text(template["css"], encoding="utf-8")
                    js_file = run_dir / "app.js"
                    if not js_file.exists() or len(js_file.read_text(encoding="utf-8", errors="ignore")) < 50:
                        js_file.write_text(template["js"], encoding="utf-8")
                except Exception:
                    pass
                return HTMLResponse(template["html"])
            return FileResponse(index_file, media_type="text/html")

        # 2. Nested index.html
        for candidate in sorted(run_dir.rglob("index.html")):
            if candidate.is_file():
                rel = candidate.relative_to(run_dir)
                return RedirectResponse(url=f"/api/preview/{run_id}/{str(rel).replace(chr(92), '/')}", status_code=307)

        # 3. Any other .html file
        for candidate in sorted(run_dir.glob("*.html")):
            if candidate.is_file():
                return FileResponse(candidate, media_type="text/html")

        # 4. If Python script exists, provide terminal runner
        py_files = sorted(run_dir.glob("*.py"))
        if py_files:
            target_name = py_files[0].name
            for cand in ("main.py", "app.py", "cli.py", "script.py"):
                if (run_dir / cand).exists():
                    target_name = cand
                    break
            return HTMLResponse(_generate_python_terminal_html(run_id, target_name))

        # 5. Default deliverables index
        return HTMLResponse(_generate_file_index_html(run_id, run_dir))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/preview/{run_id}/{file_path:path}")
def preview_file(run_id: str, file_path: str):
    """Serves individual project assets (CSS, JS, images, HTML) with accurate MIME types."""
    try:
        run_dir = _safe_resolve(WORKSPACE_DIR, run_id)
        if not run_dir.exists():
            raise HTTPException(status_code=404, detail="Run not found")

        target = _safe_resolve(run_dir, file_path)
        if not target.exists():
            # Graceful asset fallback: ensure 0 broken links or unstyled pages
            if file_path.endswith(".css"):
                from app.agents.developer import _synthesize_modern_css
                return PlainTextResponse(_synthesize_modern_css(run_id), media_type="text/css")
            elif file_path.endswith(".js"):
                from app.agents.developer import _synthesize_interactive_js
                return PlainTextResponse(_synthesize_interactive_js("", run_id), media_type="application/javascript")
            raise HTTPException(status_code=404, detail=f"File '{file_path}' not found")

        if target.is_dir():
            if (target / "index.html").exists():
                return FileResponse(target / "index.html", media_type="text/html")
            raise HTTPException(status_code=400, detail="Cannot serve directory without index.html")

        # Resolve accurate media type and validate content completeness
        if target.suffix == ".css":
            try:
                css_text = target.read_text(encoding="utf-8", errors="ignore")
                from app.agents.developer import is_css_broken, _synthesize_modern_css
                if is_css_broken(css_text):
                    synthesized = _synthesize_modern_css(run_id)
                    try:
                        target.write_text(synthesized, encoding="utf-8")
                    except Exception:
                        pass
                    return PlainTextResponse(synthesized, media_type="text/css")
            except Exception:
                pass
            return FileResponse(target, media_type="text/css")

        media_type, _ = mimetypes.guess_type(target.name)
        if target.suffix == ".js":
            media_type = "application/javascript"
        elif target.suffix == ".html":
            media_type = "text/html"
        elif target.suffix == ".json":
            media_type = "application/json"
        elif target.suffix == ".svg":
            media_type = "image/svg+xml"

        return FileResponse(target, media_type=media_type)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.api_route("/api/execute/{run_id}", methods=["GET", "POST"])
def execute_python_script(run_id: str, script: str = None):
    """Safely executes a Python script in workspace/<run_id>/ and returns execution output."""
    try:
        run_dir = _safe_resolve(WORKSPACE_DIR, run_id)
        if not run_dir.exists():
            raise HTTPException(status_code=404, detail="Run not found")

        target_script = None
        if script:
            candidate = _safe_resolve(run_dir, script)
            if candidate.exists() and candidate.is_file():
                target_script = candidate

        if not target_script:
            for cand_name in ("main.py", "app.py", "cli.py", "script.py", "index.py"):
                cand = run_dir / cand_name
                if cand.exists():
                    target_script = cand
                    break
            if not target_script:
                py_files = sorted(run_dir.glob("*.py"))
                if py_files:
                    target_script = py_files[0]

        if not target_script:
            return JSONResponse({
                "ok": False,
                "error": "No Python (.py) script found in this workspace.",
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
                "duration": 0
            })

        t0 = time.time()
        res = subprocess.run(
            [sys.executable, str(target_script.name)],
            cwd=str(run_dir),
            capture_output=True,
            text=True,
            timeout=15
        )
        duration = round(time.time() - t0, 3)
        return {
            "ok": res.returncode == 0,
            "file": target_script.name,
            "stdout": res.stdout,
            "stderr": res.stderr,
            "exit_code": res.returncode,
            "duration": duration
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "file": target_script.name if target_script else "script.py",
            "stdout": "",
            "stderr": "Execution timed out (exceeded 15s limit).",
            "exit_code": -1,
            "duration": 15.0
        }
    except Exception as exc:
        return {
            "ok": False,
            "file": target_script.name if target_script else "script.py",
            "stdout": "",
            "stderr": str(exc),
            "exit_code": -1,
            "duration": 0
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
