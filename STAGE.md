# Stage 0: Setup & Hello Graph

## Goal
Verify your Python environment, Groq Cloud API credentials, and LangGraph installation with a minimal 1-node graph.

---

## What We're Learning
- **StateGraph**: LangGraph's core abstraction for state-driven execution.
- **TypedDict State**: Defining the schema of state passed between nodes.
- **Node**: A Python function that takes the current state and returns state updates.
- **Edges (`START -> greeter -> END`)**: Controlling graph entry and termination.

---

## 1. Setup Your Environment

Make sure you have installed the dependencies:
```bash
cd backend
pip install -r requirements.txt
```

Create your `.env` file in the `backend/` directory (or workspace root):
```bash
cp .env.example .env
```
Open `.env` and fill in your Groq API key:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
MOCK_LLM=0
```
> **Note**: If you don't have an API key or want to test offline, set `MOCK_LLM=1`.

---

## 2. Run the Verification Script

Run the minimal single-node graph:
```bash
python hello_graph.py
```

### Expected Output:
```
============================================================
Tensor Bots - Stage 0: Hello Graph (Groq)
============================================================
Groq Key Set     : Yes
Model Configured : openai/gpt-oss-120b
Mock Mode Active : False
------------------------------------------------------------
[*] Node executing with prompt: 'Confirm that Tensor Bots is ready to build multi-agent systems.'...

[SUCCESS] Graph Execution Result:
Tensor Bots is fully operational and ready to build multi-agent systems!
============================================================
```

If you see `[SUCCESS] Graph Execution Result:`, your environment and Groq connection are working properly. You are ready to move to **Stage 1**!
