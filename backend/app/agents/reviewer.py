"""
LangGraph Idea: Validation & Conditional Routing (Reviewer Node)
----------------------------------------------------------------
The Reviewer demonstrates automated quality assurance and conditional graph routing:
It inspects real disk artifacts against the Planner's specifications, using
`with_structured_output(ReviewVerdict)` to output an explicit boolean verdict.
Its verdict drives the graph's conditional edge: loop back to 'developer' or proceed to 'manager_final'.
# TEACH: Notice how `ReviewVerdict` dictates whether the graph branches back or exits.
"""

import time
from pathlib import Path
from app.config import WORKSPACE_DIR, MAX_REVIEW_ROUNDS, MOCK_LLM
from app.events import emit, agent_node
from app.state import TensorState, ReviewVerdict
from app.tools import make_file_tools
from app.llm import get_llm, invoke_with_retry

REVIEWER_SYSTEM_PROMPT = """You are the Senior Code Reviewer on an AI engineering team.
Inspect the generated files on disk to determine if they satisfy the team's plan.

CRITERIA:
1. Files match the architecture plan and are non-empty.
2. Code is functional, complete, and free of glaring syntax bugs or unresolved placeholders.
3. If this is a revision iteration or the files are well-built, be pragmatic and approve!

You must return a structured verdict:
- approved: boolean (True if satisfactory, False if fixes needed)
- issues: list of short, concrete issue descriptions if rejected
- summary: single sentence verdict summary"""


@agent_node("reviewer")
def reviewer_node(state: TensorState) -> dict:
    """Evaluates project deliverables and issues structured approval or revision verdict."""
    run_id = state.get("run_id", "default_run")
    plan = state.get("plan", "")
    iteration = state.get("iteration", 1)
    
    workspace_path = WORKSPACE_DIR / run_id
    tools = make_file_tools(workspace_path)
    tools_by_name = {t.name: t for t in tools}
    
    emit("agent_status", agent="reviewer", text="Inspecting created files")
    
    # Read files from disk for review
    file_contents = {}
    if workspace_path.exists():
        for item in sorted(workspace_path.rglob("*")):
            if item.is_file():
                rel = str(item.relative_to(workspace_path))
                try:
                    file_contents[rel] = item.read_text(encoding="utf-8")[:1500]
                except Exception:
                    file_contents[rel] = "[Binary or unreadable file]"
                    
    files_summary = "\n\n".join(f"=== File: {f} ===\n{content}" for f, content in file_contents.items())
    
    if MOCK_LLM:
        time.sleep(1.0)
        # On mock mode, approve on iteration 1 if files exist
        has_files = len(file_contents) > 0
        verdict = ReviewVerdict(
            approved=has_files,
            issues=[] if has_files else ["No files found in workspace."],
            summary="All planned files exist, valid syntax verified, UI elements functional." if has_files else "Missing files."
        )
    else:
        llm = get_llm()
        structured_llm = llm.with_structured_output(ReviewVerdict)
        
        prompt_text = (
            f"{REVIEWER_SYSTEM_PROMPT}\n\n"
            f"Iteration: {iteration} of {MAX_REVIEW_ROUNDS}\n"
            f"Planned Architecture:\n{plan}\n\n"
            f"Files Found on Disk:\n{files_summary or 'NO FILES FOUND ON DISK'}"
        )
        verdict = invoke_with_retry(structured_llm, prompt_text, agent_name="reviewer")
        
        # Guardrail: force approval if maximum review cycles reached
        if iteration >= MAX_REVIEW_ROUNDS and not verdict.approved:
            verdict.approved = True
            verdict.summary += f" (Accepted at max review rounds limit: {MAX_REVIEW_ROUNDS})"

    verdict_dict = verdict.model_dump()
    
    # Emit review verdict event
    emit("review_verdict", approved=verdict.approved, issues=verdict.issues, iteration=iteration)
    
    output_md = f"""### Code Reviewer Verdict (Round {iteration})

- **Status:** {"APPROVED" if verdict.approved else "CHANGES REQUESTED"}
- **Summary:** {verdict.summary}

{"**Issues Found:**" if verdict.issues else "**No critical issues detected.**"}
{chr(10).join(f"- {i}" for i in verdict.issues)}
"""
    emit("agent_output", agent="reviewer", text=output_md)
    
    # Emit handoff particles
    if verdict.approved or iteration >= MAX_REVIEW_ROUNDS:
        emit("handoff", **{"from": "reviewer", "to": "manager", "label": "approved"})
    else:
        emit("handoff", **{"from": "reviewer", "to": "developer", "label": "changes"})
        
    return {"review": verdict_dict}
