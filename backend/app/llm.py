"""
LangGraph Idea: Pluggable Model Providers & Offline Mocking
-----------------------------------------------------------
LangGraph decouples node logic from specific foundation model vendors.
This module creates standard ChatModel instances (Google Gemini or Groq)
and supplies a Mock mode fallback so tests, workshops, and UI demos run
flawlessly offline without API keys or internet connection.
# TEACH: Agents only interact with standard BaseChatModel interfaces.
"""

import time
from typing import Any, List, Optional
from app.config import (
    LLM_PROVIDER,
    GOOGLE_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    MOCK_LLM,
    REQUEST_TIMEOUT_SECONDS,
)
from app.events import emit


def extract_text(content: Any) -> str:
    """
    Standardize message content into plain string, handling multi-part blocks or raw strings.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif hasattr(item, "text"):
                parts.append(getattr(item, "text"))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def get_llm(model_name: Optional[str] = None):
    """
    Factory function returning the configured ChatModel.
    Returns None if MOCK_LLM is enabled.
    """
    if MOCK_LLM:
        return None

    if LLM_PROVIDER == "groq" and GROQ_API_KEY:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=model_name or GROQ_MODEL,
            api_key=GROQ_API_KEY,
            temperature=0.2,
            request_timeout=REQUEST_TIMEOUT_SECONDS,
        )

    # Default provider: Google Gemini
    from langchain_google_genai import ChatGoogleGenerativeAI
    target_model = model_name or GEMINI_MODEL
    return ChatGoogleGenerativeAI(
        model=target_model,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )


def invoke_with_retry(model: Any, prompt: Any, agent_name: str = "agent", max_retries: int = 3) -> Any:
    """
    Invokes an LLM model with automatic retry on transient rate limits or quota blips.
    If a preview model hits a daily quota limit, transparently falls back to gemini-2.5-flash.
    """
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            return model.invoke(prompt)
        except Exception as exc:
            last_err = exc
            err_str = str(exc).lower()
            
            # Check for preview model daily quota exhaustion (e.g. gemini-3.8-flash limit of 20 requests/day)
            if "resource_exhausted" in err_str and ("quota" in err_str or "429" in err_str):
                emit("agent_status", agent=agent_name, text="Switching to 2.5-flash")
                try:
                    fallback_llm = get_llm(model_name="gemini-2.5-flash")
                    # If model has with_structured_output or bind_tools attached
                    if hasattr(model, "schema"):
                        fallback_target = fallback_llm.with_structured_output(getattr(model, "schema"))
                        return fallback_target.invoke(prompt)
                    elif hasattr(model, "tools"):
                        fallback_target = fallback_llm.bind_tools(getattr(model, "tools"))
                        return fallback_target.invoke(prompt)
                    else:
                        return fallback_llm.invoke(prompt)
                except Exception:
                    pass

            if attempt < max_retries and any(k in err_str for k in ("429", "rate limit", "quota", "resource exhausted", "timeout")):
                emit("agent_status", agent=agent_name, text="Rate limited, retrying...")
                time.sleep(5.0 * (attempt + 1))
            else:
                if attempt == max_retries:
                    raise
