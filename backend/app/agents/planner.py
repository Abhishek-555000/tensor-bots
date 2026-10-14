import logging
from app.events import emit, agent_node
from app.state import TensorState
from app.llm import get_llm, invoke_with_retry, extract_text

PLANNER_SYSTEM_PROMPT = """You are a software architect and UI/UX Designer on an AI development crew.
Given a user request and a brief from the Project Manager, output a clear implementation plan in markdown:
1. Target File List (STRICT REQUIREMENT: exactly 3 files: index.html, styles.css, app.js)
2. UI/UX Structure & Visual Aesthetic (layout, color scheme, typography, micro-interactions)
3. Component Breakdown & Responsibilities
4. Verification Checklist for the Reviewer

Keep your plan clear, structured, and under 250 words."""

logger = logging.getLogger(__name__)


@agent_node("planner")
def planner_node(state: TensorState) -> dict:
    """Planner agent: establishes file blueprint, component layout, and UI design using the LLM."""
    user_prompt = state.get("user_prompt", "")
    briefs = state.get("briefs", {})
    brief = briefs.get("planner", f"Create architecture plan and file breakdown for: {user_prompt}")

    emit("agent_status", agent="planner", text="Drafting architecture plan...")

    llm = get_llm()
    prompt_text = (
        f"{PLANNER_SYSTEM_PROMPT}\n\n"
        f"User Request: {user_prompt}\n"
        f"Manager Brief: {brief}"
    )
    res = invoke_with_retry(llm, prompt_text, agent_name="planner")
    plan_md = extract_text(res.content)

    emit("agent_output", agent="planner", text=plan_md)
    emit("handoff", **{"from": "planner", "to": "developer", "label": "Specs"})

    return {"plan": plan_md}
