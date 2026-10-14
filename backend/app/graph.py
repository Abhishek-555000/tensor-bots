from langgraph.graph import StateGraph, START, END
from app.state import TensorState
from app.agents.researcher import researcher_node


def build_graph():
    """
    Constructs and compiles the Stage 1 StateGraph.
    Flow: START -> researcher -> END
    """
    workflow = StateGraph(TensorState)
    
    # 1. Register researcher node
    workflow.add_node("researcher", researcher_node)
    
    # 2. Add edges
    workflow.add_edge(START, "researcher")
    workflow.add_edge("researcher", END)
    
    return workflow.compile()


# Pre-compiled graph instance
graph = build_graph()
