"""
LangGraph Idea: Tool Execution & State Joins (Developer Node)
-------------------------------------------------------------
The Developer node functions as a 'Join' barrier in the graph: it only triggers
after both parallel branches ('researcher' and 'planner') have completed.
It is equipped with sandboxed file tools (`write_file`, `read_file`, `list_files`)
and executes a tool-calling loop to write real code into `workspace/<run_id>/`.
# TEACH: Notice how `developer` reads both `research` and `plan` before acting.
"""

import time
import re
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage

from app.config import WORKSPACE_DIR, MOCK_LLM
from app.events import emit, agent_node
from app.state import TensorState
from app.tools import make_file_tools
from app.llm import get_llm, invoke_with_retry, extract_text

DEVELOPER_SYSTEM_PROMPT = """You are the Senior Software Developer on an elite AI crew.
Your job is to implement the project planned by the team using your file tools:
- write_file(path, content)
- read_file(path)
- list_files(directory)

STRICT GUARDRAILS:
1. Write at most 4 files, each under 150 lines. Keep code modular, clean, and self-contained.
2. Build standalone vanilla HTML/CSS/JavaScript or a standalone Python script. No npm/pip dependencies.
3. Every file must be complete—never leave placeholders, TODO comments, or truncated snippets.
4. If this is a revision cycle, carefully address the issues highlighted by the Reviewer.
5. YOU MUST CALL `write_file` to write each file to disk."""


def _mock_build(workspace_path: Path, prompt: str, tools_by_name: dict) -> List[str]:
    """Generate realistic, working mock project files."""
    time.sleep(1.0)
    emit("agent_status", agent="developer", text="Writing HTML markup")
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Tensor Bots - Showcase App</title>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <div class="app-card">
    <header class="header">
      <div class="logo-dot"></div>
      <h1>Project Showcase</h1>
      <span class="badge">Live</span>
    </header>
    <main class="content">
      <p class="subtitle">Prompt: {prompt}</p>
      <div class="display-box" id="timerDisplay">25:00</div>
      <div class="controls">
        <button id="startBtn" class="btn primary">Start</button>
        <button id="resetBtn" class="btn secondary">Reset</button>
      </div>
      <div class="log" id="statusLog">Status: Ready to work</div>
    </main>
  </div>
  <script src="app.js"></script>
</body>
</html>"""
    tools_by_name["write_file"].invoke({"path": "index.html", "content": html_content})

    time.sleep(0.5)
    emit("agent_status", agent="developer", text="Writing CSS stylesheet")
    css_content = """* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
body {
  background: #07040F;
  color: #E4E0F0;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
}
.app-card {
  background: #120A24;
  border: 1px solid rgba(167, 139, 250, 0.2);
  border-radius: 16px;
  padding: 32px;
  width: 90%;
  max-width: 440px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6);
}
.header { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }
.logo-dot { width: 12px; height: 12px; border-radius: 50%; background: #A78BFA; }
.badge { margin-left: auto; background: rgba(167, 139, 250, 0.15); color: #A78BFA; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
.display-box {
  background: #0B0617;
  border: 1px solid rgba(167, 139, 250, 0.15);
  font-size: 56px;
  font-weight: 700;
  color: #F472B6;
  text-align: center;
  padding: 24px;
  border-radius: 12px;
  margin: 20px 0;
  letter-spacing: 2px;
}
.controls { display: flex; gap: 12px; margin-bottom: 20px; }
.btn {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn.primary { background: #7C3AED; color: #FFF; }
.btn.primary:hover { background: #6D28D9; }
.btn.secondary { background: rgba(255, 255, 255, 0.08); color: #E4E0F0; }
.btn.secondary:hover { background: rgba(255, 255, 255, 0.12); }
.log { font-size: 13px; color: #8B84A3; text-align: center; }"""
    tools_by_name["write_file"].invoke({"path": "styles.css", "content": css_content})

    time.sleep(0.5)
    emit("agent_status", agent="developer", text="Writing JS logic")
    js_content = """let timer = null;
let seconds = 25 * 60;
let isRunning = false;

const display = document.getElementById("timerDisplay");
const startBtn = document.getElementById("startBtn");
const resetBtn = document.getElementById("resetBtn");
const statusLog = document.getElementById("statusLog");

function updateDisplay() {
  const m = Math.floor(seconds / 60).toString().padStart(2, "0");
  const s = (seconds % 60).toString().padStart(2, "0");
  display.textContent = `${m}:${s}`;
}

startBtn.addEventListener("click", () => {
  if (isRunning) {
    clearInterval(timer);
    isRunning = false;
    startBtn.textContent = "Resume";
    statusLog.textContent = "Status: Paused";
  } else {
    isRunning = true;
    startBtn.textContent = "Pause";
    statusLog.textContent = "Status: In progress...";
    timer = setInterval(() => {
      if (seconds > 0) {
        seconds--;
        updateDisplay();
      } else {
        clearInterval(timer);
        isRunning = false;
        startBtn.textContent = "Start";
        statusLog.textContent = "Status: Session finished!";
      }
    }, 1000);
  }
});

resetBtn.addEventListener("click", () => {
  clearInterval(timer);
  isRunning = false;
  seconds = 25 * 60;
  updateDisplay();
  startBtn.textContent = "Start";
  statusLog.textContent = "Status: Reset to 25m";
});"""
    tools_by_name["write_file"].invoke({"path": "app.js", "content": js_content})

    return ["index.html", "styles.css", "app.js"]


@agent_node("developer")
def developer_node(state: TensorState) -> dict:
    """Join node: executes file tools to construct or revise the requested application."""
    run_id = state.get("run_id", "default_run")
    user_prompt = state.get("user_prompt", "")
    research = state.get("research", "")
    plan = state.get("plan", "")
    review = state.get("review", {})
    iteration = state.get("iteration", 0) + 1
    
    workspace_path = WORKSPACE_DIR / run_id
    tools = make_file_tools(workspace_path)
    tools_by_name = {t.name: t for t in tools}
    
    if iteration > 1:
        emit("agent_status", agent="developer", text=f"Revision round {iteration}: fixing issues")
    else:
        emit("agent_status", agent="developer", text="Implementing planned files")
        
    created_files: List[str] = []
    
    if MOCK_LLM:
        created_files = _mock_build(workspace_path, user_prompt, tools_by_name)
    else:
        llm = get_llm()
        llm_with_tools = llm.bind_tools(tools)
        
        # Build prompt instructions with context from research, plan, and previous review
        review_context = ""
        if review and not review.get("approved", True):
            issues = review.get("issues", [])
            review_context = f"\n\nREVIEW ISSUES TO RESOLVE (Round {iteration}):\n" + "\n".join(f"- {i}" for i in issues)
            
        user_msg = (
            f"User Goal: {user_prompt}\n\n"
            f"Technical Research:\n{research}\n\n"
            f"Architecture Plan:\n{plan}"
            f"{review_context}\n\n"
            f"Please call `write_file` to create each required file now."
        )
        
        messages = [
            SystemMessage(content=DEVELOPER_SYSTEM_PROMPT),
            HumanMessage(content=user_msg),
        ]
        
        # Tool-calling loop (up to 4 rounds)
        max_tool_rounds = 4
        for round_idx in range(max_tool_rounds):
            try:
                response = invoke_with_retry(llm_with_tools, messages, agent_name="developer")
            except Exception as exc:
                # If files have already been written to disk, proceed gracefully to review
                existing_files = [p for p in workspace_path.rglob("*") if p.is_file()]
                if existing_files:
                    emit("agent_status", agent="developer", text="Files saved; handing off to reviewer")
                    break
                raise
            messages.append(response)
            
            tool_calls = getattr(response, "tool_calls", [])
            if not tool_calls:
                # If model responded with text without tool calls, inspect for code blocks fallback
                content_str = extract_text(response.content)
                code_blocks = re.findall(r"```(?:(\w+)\s+)?([^\n]+\.[a-zA-Z0-9]+)\n(.*?)```", content_str, re.DOTALL)
                if code_blocks:
                    for _, filename, code in code_blocks:
                        clean_fname = filename.strip()
                        if clean_fname and not (workspace_path / clean_fname).exists():
                            tools_by_name["write_file"].invoke({"path": clean_fname, "content": code.strip()})
                break
                
            # Execute requested tools
            for tc in tool_calls:
                tool_name = tc.get("name")
                tool_args = tc.get("args", {})
                tool_id = tc.get("id", f"call_{round_idx}")
                
                if tool_name in tools_by_name:
                    tool_func = tools_by_name[tool_name]
                    tool_result = tool_func.invoke(tool_args)
                    messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_id))
            
            # If all planned files are written, we can finish early
            disk_files = [p for p in workspace_path.rglob("*") if p.is_file()]
            if len(disk_files) >= 3:
                break
        
        # Scan workspace for all files written
        for item in sorted(workspace_path.rglob("*")):
            if item.is_file():
                created_files.append(str(item.relative_to(workspace_path)))
                
        # Fallback if no files were created: ensure at least index.html exists
        if not created_files:
            emit("agent_status", agent="developer", text="Applying fallback scaffold")
            created_files = _mock_build(workspace_path, user_prompt, tools_by_name)
    
    file_summary_lines = [f"- `{f}` ({((workspace_path / f).stat().st_size if (workspace_path / f).exists() else 0)} bytes)" for f in created_files]
    output_md = f"""### Developer Implementation (Round {iteration})

**Files Written to Disk:**
{chr(10).join(file_summary_lines) if file_summary_lines else "- No files found"}
"""
    emit("agent_output", agent="developer", text=output_md)
    emit("handoff", **{"from": "developer", "to": "reviewer", "label": "Code for review"})
    
    return {"files": created_files, "iteration": iteration}
