"""
LangGraph Idea: Parallel Worker Node (Researcher)
-------------------------------------------------
In LangGraph fan-out topologies, independent nodes can execute concurrently.
The Researcher reads its assigned brief from state, performs focused technical
investigation, and writes exclusively to the `research` key.
# TEACH: Notice how this node does not conflict with the concurrent Planner node.
"""

import time
from app.config import MOCK_LLM
from app.events import emit, agent_node
from app.state import TensorState
from app.llm import get_llm, invoke_with_retry, extract_text

RESEARCHER_SYSTEM_PROMPT = """You are a senior Technical Researcher on an AI development crew.
Given a user request and a brief from the Project Manager, output a concise technical analysis in markdown:
1. Core Architectural Constraints
2. Recommended Tech Stack & Patterns (plain HTML/CSS/JS or Python; keep it lightweight, standalone, zero npm/pip installs)
3. Key Edge Cases & Failure Modes to Avoid
4. Recommended Implementation Strategy

Keep your response under 250 words. Do not write full code implementation here (the Developer will write code)."""


@agent_node("researcher")
def researcher_node(state: TensorState) -> dict:
    """Parallel worker: evaluates technical constraints and recommended patterns."""
    user_prompt = state.get("user_prompt", "")
    briefs = state.get("briefs", {})
    brief = briefs.get("researcher", f"Research best implementation patterns for: {user_prompt}")
    
    emit("agent_status", agent="researcher", text="Analyzing tech constraints")
    
    if MOCK_LLM:
        time.sleep(1.2)
        research_md = f"""### Technical Research & Architecture Notes

- **Target Goal:** {user_prompt}
- **Stack Decision:** Vanilla HTML5, CSS3 with flexbox/grid layout, and ES6 JavaScript. No external CDNs or heavy runtimes required.
- **State Architecture:** Single state store in memory with event listeners for real-time reactivity.
- **Constraints & Risks:** Ensure high contrast, accessible controls, clean timer intervals, and responsive viewport sizing.
"""
    else:
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
