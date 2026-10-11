"""
LangGraph Idea: Configuration & Runtime Parameters
--------------------------------------------------
LangGraph applications rely on clean separation between graph architecture and
runtime configuration (model names, API keys, recursion limits, and timeouts).
This module centralizes environment variables and workspace paths so the graph
can be retargeted to different models or mock mode without altering graph code.
# TEACH: Notice how model choice and mock flags are externalized to .env.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in current directory, backend/, or parent directories
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

# Load environment variables
load_dotenv(dotenv_path=BASE_DIR / ".env")
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# LLM Provider Selection: 'gemini' or 'groq'
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower().strip()

# Gemini API configuration
# Accepts either GOOGLE_API_KEY or GEMINI_API_KEY for maximum flexibility
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
GEMINI_API_KEY = GOOGLE_API_KEY
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# Groq Cloud configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Safety net: Mock mode for offline demonstrations without API keys or internet
MOCK_LLM = os.getenv("MOCK_LLM", "0").lower().strip() in ("1", "true", "yes")

# Loop guardrails: review rounds cap
_raw_rounds = os.getenv("MAX_REVIEW_ROUNDS") or os.getenv("MAX_REVISION_ROUNDS") or "2"
try:
    MAX_REVIEW_ROUNDS = int(_raw_rounds)
except ValueError:
    MAX_REVIEW_ROUNDS = 2

# Request timeout
try:
    REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))
except ValueError:
    REQUEST_TIMEOUT_SECONDS = 60

# Workspace directory where generated projects are written
WORKSPACE_DIR = PROJECT_ROOT / "workspace"
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
