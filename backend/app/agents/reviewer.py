import logging
from app.config import WORKSPACE_DIR, MAX_REVIEW_ROUNDS
from app.events import emit, agent_node
from app.state import TensorState, ReviewVerdict
from app.llm import get_structured_llm, invoke_with_retry

REVIEWER_SYSTEM_PROMPT = """You are the Senior Code Reviewer on an AI engineering team.
Inspect the generated files on disk to determine if they satisfy the user's request and architecture plan.

CRITERIA:
1. All planned files (index.html, styles.css, app.js) exist and are non-empty.
2. Code is functional, complete, and free of glaring syntax bugs or unresolved placeholders.
3. The UI is coherent, responsive, and all interactive controls have working behavior.
4. On revisions, verify that the reported issues have been resolved.

Return a structured verdict:
- approved: boolean (True if satisfactory, False if fixes needed)
- issues: list of short, concrete issue descriptions if rejected
- summary: single sentence verdict summary"""

logger = logging.getLogger(__name__)


@agent_node("reviewer")
def reviewer_node(state: TensorState) -> dict:
    """Reviewer agent: inspects files on disk and evaluates quality using the LLM."""
    run_id = state.get("run_id", "default_run")
    user_prompt = state.get("user_prompt", "")
    plan = state.get("plan", "")
    iteration = state.get("iteration", 1)
    workspace_path = WORKSPACE_DIR / run_id

    emit("agent_status", agent="reviewer", text="Inspecting created files...")

    file_contents = {}
    if workspace_path.exists():
        for item in sorted(workspace_path.rglob("*")):
            if item.is_file():
                rel = str(item.relative_to(workspace_path))
                try:
                    file_contents[rel] = item.read_text(encoding="utf-8")[:3000]
                except Exception:
                    file_contents[rel] = "[Binary or unreadable file]"

    files_summary = "\n\n".join(f"=== File: {f} ===\n{content}" for f, content in file_contents.items())

    structured_llm = get_structured_llm(ReviewVerdict)
    prompt_text = (
        f"{REVIEWER_SYSTEM_PROMPT}\n\n"
        f"Original User Request:\n{user_prompt}\n\n"
        f"Iteration: {iteration} of {MAX_REVIEW_ROUNDS}\n"
        f"Planned Architecture:\n{plan}\n\n"
        f"Files Found on Disk:\n{files_summary or 'NO FILES FOUND ON DISK'}"
    )

    verdict = invoke_with_retry(structured_llm, prompt_text, agent_name="reviewer", schema=ReviewVerdict)
    verdict_dict = verdict.model_dump()

    emit(
        "review_verdict",
        approved=verdict.approved,
        issues=verdict.issues,
        iteration=iteration,
        verification_unavailable=False,
    )

    output_md = f"""### Code Reviewer Verdict (Round {iteration})

- **Status:** {"APPROVED" if verdict.approved else "CHANGES REQUESTED"}
- **Summary:** {verdict.summary}

{"**Issues Found:**" if verdict.issues else "**No critical issues detected.**"}
{chr(10).join(f"- {i}" for i in verdict.issues)}
"""
    emit("agent_output", agent="reviewer", text=output_md)

    if verdict.approved:
        emit("handoff", **{"from": "reviewer", "to": "manager", "label": "approved"})
    elif iteration >= MAX_REVIEW_ROUNDS:
        emit("handoff", **{"from": "reviewer", "to": "manager", "label": "review limit reached"})
    else:
        emit("handoff", **{"from": "reviewer", "to": "developer", "label": "changes"})

    return {"review": verdict_dict}
