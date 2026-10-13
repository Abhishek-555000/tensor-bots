import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in current directory, backend/, or parent directories
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

# Load environment variables: root .env takes precedence for user secrets
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)


def _clean_key(val: str | None) -> str:
    """Filter out boilerplate placeholder strings from template .env files."""
    if not val:
        return ""
    v = val.strip()
    if v.startswith("your_") or "api_key_here" in v:
        return ""
    return v


# Gemini API configuration
GOOGLE_API_KEY = _clean_key(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
GEMINI_API_KEY = GOOGLE_API_KEY
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

# Groq Cloud configuration
GROQ_API_KEY = _clean_key(os.getenv("GROQ_API_KEY"))
raw_groq_model = os.getenv("GROQ_MODEL", "").strip()
# Use openai/gpt-oss-120b by default for high token limits, tool calling & complete generation
if not raw_groq_model or raw_groq_model in ("llama-3.3-70b-versatile", "qwen/qwen3.8-27b"):
    GROQ_MODEL = "openai/gpt-oss-120b"
else:
    GROQ_MODEL = raw_groq_model

# LLM Provider Selection: automatically route to provider with active key
env_provider = os.getenv("LLM_PROVIDER", "").lower().strip()
if env_provider == "groq" and GROQ_API_KEY:
    LLM_PROVIDER = "groq"
elif env_provider == "gemini" and GOOGLE_API_KEY:
    LLM_PROVIDER = "gemini"
elif GROQ_API_KEY:
    LLM_PROVIDER = "groq"
elif GOOGLE_API_KEY:
    LLM_PROVIDER = "gemini"
else:
    LLM_PROVIDER = "gemini"

# Safety net: Mock mode for offline demonstrations without API keys or internet
raw_mock = os.getenv("MOCK_LLM", "").lower().strip()
if raw_mock in ("1", "true", "yes"):
    MOCK_LLM = True
elif raw_mock in ("0", "false", "no"):
    MOCK_LLM = False
else:
    # If no valid keys exist, automatically engage mock mode
    has_valid_key = bool(GOOGLE_API_KEY or GROQ_API_KEY)
    MOCK_LLM = not has_valid_key

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
