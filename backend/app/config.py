"""
Tensor Bots - Configuration and Environment Settings.

# TEACH: Manages LLM credentials (Groq), models, timeouts, and sandboxed paths.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in current directory, backend/, or parent directories
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

# Load environment variables: shell environment takes precedence, then .env files
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=False)
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)


def _clean_key(val: str | None) -> str:
    """Filter out boilerplate placeholder strings from template .env files."""
    if not val:
        return ""
    v = val.strip()
    if v.startswith("your_") or "api_key_here" in v:
        return ""
    return v


# Groq Cloud configuration
GROQ_API_KEY = _clean_key(os.getenv("GROQ_API_KEY"))
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
LLM_PROVIDER = "groq"

# Safety net: Mock mode for offline demonstrations without API keys or internet
raw_mock = os.getenv("MOCK_LLM", "").lower().strip()
if raw_mock in ("1", "true", "yes"):
    MOCK_LLM = True
elif raw_mock in ("0", "false", "no"):
    MOCK_LLM = False
else:
    # If no valid Groq key exists, automatically engage mock mode
    has_valid_key = bool(GROQ_API_KEY)
    MOCK_LLM = not has_valid_key
    if MOCK_LLM:
        print("[WARN] No Groq API key found, running in MOCK mode")

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
