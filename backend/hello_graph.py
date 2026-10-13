import os
import sys
from pathlib import Path
from typing import TypedDict
from dotenv import load_dotenv

# Ensure local app packages can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Load .env
load_dotenv(".env")
load_dotenv("../.env")

from langgraph.graph import StateGraph, START, END
from app.config import MOCK_LLM, GEMINI_MODEL, GOOGLE_API_KEY
from app.llm import get_llm, extract_text


class HelloState(TypedDict):
    prompt: str
    reply: str


def greet_node(state: HelloState) -> dict:
    """A single node that invokes the LLM to verify connectivity."""
    prompt = state.get("prompt", "Say hello in one enthusiastic sentence!")
    print(f"[*] Node executing with prompt: '{prompt}'...")
    
    if MOCK_LLM:
        reply = "Hello from Mock Tensor Bots! Environment and LangGraph are working perfectly."
    else:
        llm = get_llm()
        res = llm.invoke(f"You are a friendly multi-agent assistant. {prompt}")
        reply = extract_text(res.content)
    
    return {"reply": reply}


def main():
    print("=" * 60)
    print("Tensor Bots - Stage 0: Hello Graph")
    print("=" * 60)
    print(f"Provider Key Set : {'Yes' if GOOGLE_API_KEY else 'No'}")
    print(f"Model Configured : {GEMINI_MODEL}")
    print(f"Mock Mode Active : {MOCK_LLM}")
    print("-" * 60)
    
    # 1. Initialize StateGraph
    builder = StateGraph(HelloState)
    
    # 2. Add single node
    builder.add_node("greeter", greet_node)
    
    # 3. Connect START -> greeter -> END
    builder.add_edge(START, "greeter")
    builder.add_edge("greeter", END)
    
    # 4. Compile graph
    graph = builder.compile()
    
    # 5. Invoke graph
    initial_state: HelloState = {"prompt": "Confirm that Tensor Bots is ready to build multi-agent systems.", "reply": ""}
    final_state = graph.invoke(initial_state)
    
    print("\n[SUCCESS] Graph Execution Result:")
    print(final_state["reply"])
    print("=" * 60)


if __name__ == "__main__":
    main()
