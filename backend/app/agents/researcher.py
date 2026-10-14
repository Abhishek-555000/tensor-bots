import logging
from app.events import emit, agent_node
from app.state import TensorState
from app.llm import get_llm, invoke_with_retry, extract_text

RESEARCHER_SYSTEM_PROMPT = """You are a senior Technical Researcher on an AI development crew.
Given a user request and a brief from the Project Manager, output a concise technical analysis in markdown:
1. Core Architectural Constraints
2. Recommended Tech Stack & Patterns (vanilla HTML/CSS/JS; lightweight, standalone, zero npm/pip installs)
3. Key Edge Cases & Failure Modes to Avoid
4. Recommended Implementation Strategy

Keep your response under 250 words."""

logger = logging.getLogger(__name__)


@agent_node("researcher")
def researcher_node(state: TensorState) -> dict:
    """Researcher agent: analyzes technical constraints and patterns using the LLM."""
    user_prompt = state.get("user_prompt", "")
    briefs = state.get("briefs", {})
    brief = briefs.get("researcher", f"Research best implementation patterns for: {user_prompt}")

    emit("agent_status", agent="researcher", text="Analyzing tech constraints...")

    llm = get_llm()
    prompt_text = (
        f"{RESEARCHER_SYSTEM_PROMPT}\n\n"
        f"User Request: {user_prompt}\n"
        f"Manager Brief: {brief}"
    )
    res = invoke_with_retry(llm, prompt_text, agent_name="researcher")
    research_md = extract_text(res.content)

    emit("agent_output", agent="researcher", text=research_md)
    emit("handoff", **{"from": "researcher", "to": "developer", "label": "Findings"})

    return {"research": research_md}
