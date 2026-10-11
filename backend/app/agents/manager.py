"""
LangGraph Idea: Structured Output & Dispatching (Manager Node)
--------------------------------------------------------------
The Project Manager demonstrates two essential LangGraph concepts:
1. Structured Outputs: Using `with_structured_output(AgentBriefs)` to constrain
   the LLM into generating typed, validated task specifications for teammates.
2. Dual Lifecycle Nodes: The manager node acts as both the entry dispatcher
   (`manager_plan`) and the final synthesizer (`manager_final`), sharing the same
   identity in telemetry and UI.
# TEACH: Notice how `with_structured_output` guarantees typed downstream inputs.
"""

import time
from app.config import MOCK_LLM
from app.events import emit, agent_node
from app.state import TensorState, AgentBriefs
from app.llm import get_llm, invoke_with_retry, extract_text

MANAGER_SYSTEM_PROMPT = """You are the Project Manager of an elite engineering crew.
Your goal is to break down the user request into 4 concise, targeted briefs for your teammates:
1. Researcher: 1-3 sentences focusing on key constraints, best practices, tech stack decisions.
2. Planner: 1-3 sentences focusing on file structure (<= 4 files), visual design, UX requirements.
3. Developer: 1-3 sentences focusing on implementation details, simplicity, clean code.
4. Reviewer: 1-3 sentences focusing on what to inspect, quality standards, completeness checks.

Keep all briefs direct, professional, and practical."""

FINAL_SUMMARY_SYSTEM_PROMPT = """You are the Project Manager wrapping up the completed project.
Write a clear, inspiring 3-5 line summary of what was built, followed by a bulleted list of created files.
Keep it succinct, user-friendly, and polished."""


@agent_node("manager")
def manager_plan(state: TensorState) -> dict:
    """Entry node: breaks down the user prompt and dispatches briefs to the team."""
    user_prompt = state.get("user_prompt", "").strip() or "Build a modern interactive web application."
    
    emit("agent_status", agent="manager", text="Decomposing user request")
    
    # Notify UI that downstream agents will be waiting on prerequisites
    emit("agent_waiting", agent="developer", on=["researcher", "planner"])
    emit("agent_waiting", agent="reviewer", on=["developer"])
    
    if MOCK_LLM:
        time.sleep(1.0)
        briefs = AgentBriefs(
            researcher=f"Investigate core UI patterns, reactive state handling, and accessible styling for: '{user_prompt}'. Keep stack to vanilla HTML/JS/CSS.",
            planner=f"Plan a clean modular structure of at most 3 files (index.html, styles.css, app.js) with dark aesthetics and smooth interactions.",
            developer=f"Implement fully functional, self-contained code for all planned files. Ensure responsive layout and complete logic.",
            reviewer=f"Verify all planned files exist, buttons respond correctly, styling renders properly, and no placeholders remain."
        )
    else:
        llm = get_llm()
        structured_llm = llm.with_structured_output(AgentBriefs)
        prompt_text = f"{MANAGER_SYSTEM_PROMPT}\n\nUser Request: {user_prompt}"
        briefs = invoke_with_retry(structured_llm, prompt_text, agent_name="manager")
    
    briefs_dict = briefs.model_dump()
    
    # Format readable output for the UI slide-over detail panel
    output_md = f"""### Project Manager Task Briefs

**Objective:** {user_prompt}

- **Researcher:** {briefs.researcher}
- **Planner:** {briefs.planner}
- **Developer:** {briefs.developer}
- **Reviewer:** {briefs.reviewer}
"""
    emit("agent_output", agent="manager", text=output_md)
    
    # Emit handoff particles for parallel fan-out
    emit("handoff", **{"from": "manager", "to": "researcher", "label": "Research brief"})
    emit("handoff", **{"from": "manager", "to": "planner", "label": "Plan brief"})
    
    return {"briefs": briefs_dict}


@agent_node("manager_final")
def manager_final(state: TensorState) -> dict:
    """Exit node: generates user-facing wrap-up summary after reviewer approval."""
    user_prompt = state.get("user_prompt", "")
    files = state.get("files", [])
    plan = state.get("plan", "")
    review = state.get("review", {})
    
    emit("agent_status", agent="manager", text="Finalizing project delivery")
    
    files_list_str = "\n".join(f"- `{f}`" for f in files) if files else "- No files recorded"
    
    if MOCK_LLM:
        time.sleep(0.8)
        summary = (
            f"Successfully built and verified project for: '{user_prompt}'.\n"
            f"All components have been verified and approved by the Reviewer.\n\n"
            f"**Deliverables:**\n{files_list_str}"
        )
    else:
        llm = get_llm()
        prompt_text = (
            f"{FINAL_SUMMARY_SYSTEM_PROMPT}\n\n"
            f"Original Request: {user_prompt}\n"
            f"Reviewer Verdict: {review.get('summary', 'Approved')}\n"
            f"Files Created:\n{files_list_str}\n"
        )
        res = invoke_with_retry(llm, prompt_text, agent_name="manager")
        summary = extract_text(res.content)
    
    emit("agent_output", agent="manager", text=summary)
    emit("run_finished", summary=summary, files=files)
    
    return {"final_summary": summary}
