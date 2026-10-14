from langgraph.graph import StateGraph, START, END
from app.state import TensorState
from app.agents.manager import manager_plan
from app.agents.researcher import researcher_node


def build_graph():
    """
    Constructs and compiles the Stage 2 StateGraph.
    Flow: START -> manager -> researcher -> END
    """
    workflow = StateGraph(TensorState)
    
    # 1. Register nodes
    workflow.add_node("manager", manager_plan)
    workflow.add_node("researcher", researcher_node)
    
    # 2. Add edges
    workflow.add_edge(START, "manager")
    workflow.add_edge("manager", "researcher")
    workflow.add_edge("researcher", END)
    
    return workflow.compile()


# Pre-compiled graph instance
graph = build_graph()
