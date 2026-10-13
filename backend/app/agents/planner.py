import time
import logging
from app.config import MOCK_LLM
from app.events import emit, agent_node
from app.state import TensorState
from app.llm import get_llm, invoke_with_retry, extract_text

PLANNER_SYSTEM_PROMPT = """You are a software architect and UI/UX Designer on an AI development crew.
Given a user request and a brief from the Project Manager, output a clear implementation plan in markdown:
1. Target File List (STRICT REQUIREMENT: at most 4 files, e.g. index.html, styles.css, app.js or script.py)
2. UI/UX Structure & Visual Aesthetic (layout, color scheme, typography, micro-interactions)
3. Component Breakdown & Responsibilities
4. Verification Checklist for the Reviewer

Keep your plan clear, structured, and under 250 words."""
logger = logging.getLogger(__name__)


@agent_node("planner")
def planner_node(state: TensorState) -> dict:
    """Parallel worker: establishes file blueprint, component layout, and UI design."""
    user_prompt = state.get("user_prompt", "")
    briefs = state.get("briefs", {})
    brief = briefs.get("planner", f"Create architecture plan and file breakdown for: {user_prompt}")
    
    emit("agent_status", agent="planner", text="Drafting architecture plan")
    
    if MOCK_LLM:
        time.sleep(1.4)
        plan_md = f"""### Implementation Architecture & Design Plan

#### 1. Planned Files (3 files maximum)
- `index.html`: Semantic markup containing the core container, header, controls, and display.
- `styles.css`: Dark-mode aesthetics (`#0a0714` background, violet accents, crisp typography).
- `app.js`: State management, event handlers, and active timer/calculation logic.

#### 2. Design System
- Modern dark mode with subtle border glows and responsive card layout.
- Clean typography and intuitive touch/click targets.

#### 3. Verification Criteria
- All 3 files present on disk.
- Interactive controls functional with zero console errors.
"""
    else:
        try:
            llm = get_llm()
            prompt_text = (
                f"{PLANNER_SYSTEM_PROMPT}\n\n"
                f"User Request: {user_prompt}\n"
                f"Manager Brief: {brief}"
            )
            res = invoke_with_retry(llm, prompt_text, agent_name="planner")
            plan_md = extract_text(res.content)
        except Exception as exc:
            logger.warning(
                "Planner model failed (%s); continuing with baseline plan",
                type(exc).__name__,
            )
            emit("agent_status", agent="planner", text="Using baseline implementation plan")
            plan_md = (
                f"### Implementation Plan\n\n"
                f"- **Goal:** {user_prompt}\n"
                "- **Files:** Use a small standalone HTML/CSS/JavaScript project unless the request "
                "specifically calls for a script.\n"
                "- **Design:** Build a responsive interface around the main user task with clear "
                "feedback and accessible controls.\n"
                "- **Verification:** Exercise the main workflow, edge cases, keyboard behavior, and "
                "all visible controls.\n"
                f"- **Provider note:** Planning generation was unavailable ({type(exc).__name__}); "
                "the implementation will continue using this baseline."
            )
    
    emit("agent_output", agent="planner", text=plan_md)
    emit("handoff", **{"from": "planner", "to": "developer", "label": "Specs"})
    
    return {"plan": plan_md}
