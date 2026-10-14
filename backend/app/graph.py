from langgraph.graph import StateGraph, START, END
from app.state import TensorState
from app.agents.manager import manager_plan
from app.agents.researcher import researcher_node
from app.agents.planner import planner_node
from app.agents.developer import developer_node


def build_graph():
    """
    Constructs and compiles the Stage 3 StateGraph.
    Flow:
      START -> manager -> [researcher, planner] (parallel fan-out)
      [researcher, planner] -> developer (fan-in / join) -> END
    """
    workflow = StateGraph(TensorState)
    
    # 1. Register nodes
    workflow.add_node("manager", manager_plan)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("developer", developer_node)
    
    # 2. Add entry edge
    workflow.add_edge(START, "manager")
    
    # 3. Parallel Fan-Out: Manager dispatches to Researcher and Planner simultaneously
    workflow.add_edge("manager", "researcher")
    workflow.add_edge("manager", "planner")
    
    # 4. Fan-In / Join: Developer node waits until BOTH Researcher and Planner have finished
    workflow.add_edge(["researcher", "planner"], "developer")
    
    # 5. Developer to END
    workflow.add_edge("developer", END)
    
    return workflow.compile()


# Pre-compiled graph instance
graph = build_graph()
