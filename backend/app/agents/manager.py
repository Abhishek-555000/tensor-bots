import logging
from app.events import emit, agent_node
from app.state import TensorState, AgentBriefs
from app.llm import get_structured_llm, invoke_with_retry

MANAGER_SYSTEM_PROMPT = """You are the Project Manager of an elite engineering crew.
Your goal is to break down the user request into 4 concise, targeted briefs for your teammates:
1. Researcher: 1-3 sentences focusing on key constraints, best practices, tech stack decisions.
2. Planner: 1-3 sentences focusing on file structure (index.html, styles.css, app.js), visual design, UX requirements.
3. Developer: 1-3 sentences focusing on implementation details, simplicity, clean code.
4. Reviewer: 1-3 sentences focusing on what to inspect, quality standards, completeness checks.

Keep all briefs direct, professional, and practical."""

logger = logging.getLogger(__name__)


@agent_node("manager")
def manager_plan(state: TensorState) -> dict:
    """Entry node: breaks down the user prompt and dispatches structured briefs to teammates."""
    user_prompt = state.get("user_prompt", "").strip() or "Build a modern interactive web application."

    emit("agent_status", agent="manager", text="Decomposing user request...")
    emit("agent_waiting", agent="developer", on=["researcher", "planner"])
    emit("agent_waiting", agent="reviewer", on=["developer"])

    structured_llm = get_structured_llm(AgentBriefs)
    prompt_text = f"{MANAGER_SYSTEM_PROMPT}\n\nUser Request: {user_prompt}"
    briefs = invoke_with_retry(structured_llm, prompt_text, agent_name="manager", schema=AgentBriefs)
    briefs_dict = briefs.model_dump()

    output_md = f"""### Project Manager Task Briefs

**Objective:** {user_prompt}

- **Researcher:** {briefs.researcher}
- **Planner:** {briefs.planner}
- **Developer:** {briefs.developer}
- **Reviewer:** {briefs.reviewer}
"""
    emit("agent_output", agent="manager", text=output_md)
    emit("handoff", **{"from": "manager", "to": "researcher", "label": "Research brief"})

    return {"briefs": briefs_dict}
