import logging
from app.events import emit, agent_node
from app.state import TensorState

logger = logging.getLogger(__name__)


@agent_node("developer")
def developer_node(state: TensorState) -> dict:
    """Stage 3 Developer Stub: Verifies that both Researcher and Planner outputs have arrived."""
    research = state.get("research", "")
    plan = state.get("plan", "")

    emit("agent_status", agent="developer", text="Gathered inputs from Researcher and Planner...")

    summary = f"""### Developer Node (Stage 3 Join Verification)

- **Received Research:** {len(research)} characters
- **Received Architecture Plan:** {len(plan)} characters
- **Status:** Both parallel branches successfully joined into Developer node!
"""
    emit("agent_output", agent="developer", text=summary)
    emit("handoff", **{"from": "developer", "to": "reviewer", "label": "Draft specs"})

    return {"files": ["index.html (stub)"]}
