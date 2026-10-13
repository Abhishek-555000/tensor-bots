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
    OPENAI_API_KEY,
    OPENAI_MODEL,
    MOCK_LLM,
    REQUEST_TIMEOUT_SECONDS,
)
from app.events import emit

def _retryable_model_error(exc: Exception) -> bool:
    """Return True for quota, throttle, access, or missing-model errors that are safe to retry on another backend."""
    if exc is None:
        return False
    err_str = str(exc).lower()
    return any(
        token in err_str
        for token in (
            "429",
            "rate limit",
            "rate_limit",
            "quota",
            "resource_exhausted",
            "too many requests",
            "daily quota",
            "exceeded",
            "timeout",
            "model not found",
            "does not exist",
            "not available",
            "access denied",
            "not found",
            "invalid model",
            "decommissioned",
            "deprecated",
            "unsupported",
        )
    )


def _fallback_models_for(model_name: Optional[str]) -> list[str]:
    """Return provider-aligned backups for transient quota exhaustion or unavailable models."""
    base_model = (model_name or "").strip()
    if LLM_PROVIDER == "groq":
        pool = [
            "llama-3.1-8b-instant",
            "llama-3.3-70b-versatile",
        ]
    elif LLM_PROVIDER == "openai":
        pool = [
            "gpt-4o-mini",
            "gpt-4.1-mini",
            "openai/gpt-oss-20b",
        ]
    else:
        pool = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
        ]
    if base_model:
        pool = [item for item in pool if item != base_model]
    return list(dict.fromkeys(pool))


def _bind_model_for_target(model: Any, target_llm: Any) -> Any:
    """Retarget a model to a different LLM instance while preserving tool/schema settings."""
    if hasattr(model, "schema"):
        return target_llm.with_structured_output(getattr(model, "schema"))
    if hasattr(model, "tools"):
        return target_llm.bind_tools(getattr(model, "tools"))
    return target_llm


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

    if LLM_PROVIDER == "openai" and OPENAI_API_KEY:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name or OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0.2,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

    # Default provider: Google Gemini
    if not GOOGLE_API_KEY:
        raise RuntimeError(
            "No API key configured for Gemini. Set GOOGLE_API_KEY or GEMINI_API_KEY, or enable MOCK_LLM=1."
        )
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
    Invoke a model with light retry logic and safe fallback between provider-aligned models.
    When quota or rate limiting is detected, transparently try a different supported model
    before surfacing the error to the graph.
    """
    last_err = None
    tried_models: set[str] = set()
    fallback_names = _fallback_models_for(getattr(model, "model_name", None) or getattr(model, "model", None))
    for attempt in range(max_retries + 1):
        try:
            return model.invoke(prompt)
        except Exception as exc:
            last_err = exc
            if not _retryable_model_error(exc):
                if attempt == max_retries:
                    raise
                continue

            emit("agent_status", agent=agent_name, text="Model unavailable; trying backup model...")
            for alt_model_name in fallback_names:
                if alt_model_name in tried_models:
                    continue
                tried_models.add(alt_model_name)
                try:
                    alt_llm = get_llm(model_name=alt_model_name)
                    alt_model = _bind_model_for_target(model, alt_llm)
                    emit("agent_status", agent=agent_name, text=f"Trying fallback model: {alt_model_name}")
                    return alt_model.invoke(prompt)
                except Exception as alt_exc:
                    last_err = alt_exc
                    if not _retryable_model_error(alt_exc):
                        raise
                    emit("agent_status", agent=agent_name, text=f"Fallback model {alt_model_name} unavailable; trying next option...")

            if attempt < max_retries:
                time.sleep(2.0 * (attempt + 1))
                continue

            raise RuntimeError(
                f"LLM provider exhausted for {agent_name}; all backup models are unavailable or quota-blocked."
            ) from last_err
