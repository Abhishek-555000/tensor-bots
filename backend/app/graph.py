from langgraph.graph import StateGraph, START, END
from app.config import MAX_REVIEW_ROUNDS
from app.state import TensorState
from app.agents.manager import manager_plan, manager_final
from app.agents.researcher import researcher_node
from app.agents.planner import planner_node
from app.agents.developer import developer_node
from app.agents.reviewer import reviewer_node


def route_review(state: TensorState) -> str:
    """
    Conditional routing function for the reviewer's verdict.
    
    # Stop after approval, review exhaustion, or an unavailable review provider.
    # Otherwise, loop back to developer for another revision round.
    """
    review = state.get("review", {})
    iteration = state.get("iteration", 1)
    
    is_approved = review.get("approved", False)
    if review.get("verification_unavailable"):
        return "manager_final"
    if is_approved or iteration >= MAX_REVIEW_ROUNDS:
        return "manager_final"
    return "developer"


def build_graph():
    """Constructs and compiles the TensorState StateGraph."""
    workflow = StateGraph(TensorState)
    
    # 1. Register agent nodes
    workflow.add_node("manager", manager_plan)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("developer", developer_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("manager_final", manager_final)
    
    # 2. Add entry edge
    workflow.add_edge(START, "manager")
    
    # 3. Parallel Fan-Out: Manager dispatches to Researcher and Planner simultaneously
    workflow.add_edge("manager", "researcher")
    workflow.add_edge("manager", "planner")
    
    # 4. Fan-In / Join: Developer node waits until BOTH Researcher and Planner have finished
    workflow.add_edge(["researcher", "planner"], "developer")
    
    # 5. Developer hands off to Reviewer
    workflow.add_edge("developer", "reviewer")
    
    # 6. Conditional Edge: Loop back for changes or exit on approval / max rounds
    workflow.add_conditional_edges(
        "reviewer",
        route_review,
        {
            "developer": "developer",
            "manager_final": "manager_final",
        }
    )
    
    # 7. Final manager wraps up and terminates the graph
    workflow.add_edge("manager_final", END)
    
    return workflow.compile()


# Pre-compiled graph instance
graph = build_graph()
