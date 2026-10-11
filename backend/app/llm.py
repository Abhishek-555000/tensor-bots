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

# Cascade of resilient Gemini models with independent free-tier quota pools
GEMINI_FALLBACK_POOL = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.7-flash"]


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


def invoke_with_retry(model: Any, prompt: Any, agent_name: str = "agent", max_retries: int = 2) -> Any:
    """
    Invokes an LLM model with automatic retry and intelligent fallback across the model pool
    if a preview model's daily free-tier quota is exhausted.
    """
    last_err = None
    
    # Try with primary model
    for attempt in range(max_retries + 1):
        try:
            return model.invoke(prompt)
        except Exception as exc:
            last_err = exc
            err_str = str(exc).lower()

            # Quota exhausted: cascade through the Gemini model pool
            if "resource_exhausted" in err_str or "quota" in err_str or "429" in err_str:
                for alt_model in GEMINI_FALLBACK_POOL:
                    try:
                        emit("agent_status", agent=agent_name, text=f"Trying {alt_model}...")
                        alt_llm = get_llm(model_name=alt_model)
                        if hasattr(model, "schema"):
                            alt_target = alt_llm.with_structured_output(getattr(model, "schema"))
                            return alt_target.invoke(prompt)
                        elif hasattr(model, "tools"):
                            alt_target = alt_llm.bind_tools(getattr(model, "tools"))
                            return alt_target.invoke(prompt)
                        else:
                            return alt_llm.invoke(prompt)
                    except Exception as alt_exc:
                        alt_err = str(alt_exc).lower()
                        if "resource_exhausted" in alt_err or "quota" in alt_err:
                            continue
                        raise alt_exc

            if attempt < max_retries and any(k in err_str for k in ("429", "rate limit", "quota", "timeout")):
                emit("agent_status", agent=agent_name, text="Rate limited, retrying...")
                time.sleep(4.0 * (attempt + 1))
            else:
                if attempt == max_retries:
                    raise last_err
