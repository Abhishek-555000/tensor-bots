"""
LangGraph Idea: Graph Topology, Fan-Out, Join & Cycles
------------------------------------------------------
This file defines the complete StateGraph wiring:
1. Entry point: `START -> manager`
2. Fan-out: `manager -> researcher` and `manager -> planner` in parallel
3. Join: `researcher -> developer` and `planner -> developer` (waits for both!)
4. Sequential: `developer -> reviewer`
5. Conditional routing: `reviewer -> developer` (re-try loop) OR `reviewer -> manager_final` (exit)
6. Termination: `manager_final -> END`
# TEACH: In LangGraph, adding edges from multiple nodes to one creates an automatic join barrier!
"""

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
    
    # TEACH: If approved or review rounds hit the cap, proceed to manager_final.
    # Otherwise, loop back to developer for another revision round.
    """
    review = state.get("review", {})
    iteration = state.get("iteration", 1)
    
    is_approved = review.get("approved", False)
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
    
    # 4. Join: Developer node waits until BOTH Researcher and Planner have finished
    workflow.add_edge("researcher", "developer")
    workflow.add_edge("planner", "developer")
    
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
