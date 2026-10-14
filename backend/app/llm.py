"""
Tensor Bots - Groq LLM Factory and Invocation Pipeline.

# TEACH: Connects agents to Groq Cloud LLMs with automatic retry,
# fallback pooling, and deterministic offline mock simulation.
"""

import time
import logging
from typing import Any, List, Optional
from app.config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    MOCK_LLM,
    REQUEST_TIMEOUT_SECONDS,
)
from app.events import emit
from app.mock import mock_response

# Groq fallback pool of resilient models
GROQ_FALLBACK_POOL = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
logger = logging.getLogger(__name__)


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
    Factory function returning the configured Groq ChatModel.
    Returns None if MOCK_LLM is enabled.
    """
    if MOCK_LLM:
        return None

    from langchain_groq import ChatGroq
    target_model = model_name or GROQ_MODEL
    return ChatGroq(
        model=target_model,
        api_key=GROQ_API_KEY,
        temperature=0.2,
        max_tokens=8192,
        request_timeout=REQUEST_TIMEOUT_SECONDS,
    )


def get_structured_llm(schema: Any, model_name: Optional[str] = None):
    """
    Factory creating a structured-output ChatModel via Groq.
    Explicitly uses method='json_schema' to ensure clean schema compliance.
    """
    if MOCK_LLM:
        return None
    llm = get_llm(model_name=model_name)
    return llm.with_structured_output(schema, method="json_schema")


def invoke_with_retry(
    model: Any,
    prompt: Any,
    agent_name: str = "agent",
    schema: Optional[Any] = None,
    max_retries: int = 2,
    tools: Optional[list[Any]] = None,
) -> Any:
    """
    Invokes a Groq model with automatic retry and intelligent fallback across the model pool
    if a model's quota is exhausted, rate limited, or unavailable.
    """
    if MOCK_LLM:
        return mock_response(agent_name=agent_name, schema=schema, prompt=prompt)

    last_err: Exception | None = None
    fallback_pool = GROQ_FALLBACK_POOL
    primary_model = GROQ_MODEL
    fallback_attempted = False
    
    # Try with primary model
    for attempt in range(max_retries + 1):
        try:
            return model.invoke(prompt)
        except Exception as exc:
            last_err = exc
            err_str = str(exc).lower()

            # Quota exhausted, rate limited, or model error: cascade through fallback pool
            if not fallback_attempted and any(
                k in err_str
                for k in (
                    "resource_exhausted",
                    "quota",
                    "429",
                    "model_not_found",
                    "not exist",
                    "tool_use_failed",
                    "tool choice is required",
                    "tool_choice",
                    "timeout",
                    "timed out",
                    "connection",
                    "service unavailable",
                    "internal server error",
                    "502",
                    "503",
                    "504",
                )
            ):
                fallback_attempted = True
                seen_models = {primary_model}
                for alt_model in fallback_pool:
                    if alt_model in seen_models:
                        continue
                    seen_models.add(alt_model)
                    try:
                        emit("agent_status", agent=agent_name, text=f"Trying {alt_model}...")
                        if schema is not None:
                            alt_target = get_structured_llm(schema, model_name=alt_model)
                            return alt_target.invoke(prompt)
                        else:
                            alt_llm = get_llm(model_name=alt_model)
                            if tools is not None:
                                alt_llm = alt_llm.bind_tools(tools)
                            return alt_llm.invoke(prompt)
                    except Exception as alt_exc:
                        last_err = alt_exc
                        logger.warning(
                            "Fallback model %s failed for %s (%s)",
                            alt_model,
                            agent_name,
                            type(alt_exc).__name__,
                        )

                if schema is not None:
                    try:
                        raw_llm = get_llm()
                        json_prompt = f"{prompt}\n\nOutput STRICT JSON matching schema without any markdown or tool calls."
                        res = raw_llm.invoke(json_prompt)
                        raw_txt = extract_text(res.content)
                        import json, re
                        m = re.search(r"(\{.*\})", raw_txt, re.DOTALL)
                        if m:
                            return schema.model_validate(json.loads(m.group(1)))
                    except Exception as raw_exc:
                        last_err = raw_exc
                        logger.warning(
                            "Structured-output fallback failed for %s: %s",
                            agent_name,
                            raw_exc,
                        )
                raise last_err

            if attempt < max_retries and any(k in err_str for k in ("429", "rate limit", "quota", "timeout")):
                emit("agent_status", agent=agent_name, text="Rate limited, retrying...")
                time.sleep(2.0 * (attempt + 1))
            else:
                if attempt == max_retries:
                    # Final safety net for structured schemas: raw JSON extraction
                    if schema is not None:
                        try:
                            raw_llm = get_llm()
                            json_prompt = f"{prompt}\n\nOutput STRICT JSON matching schema without any markdown or tool calls."
                            res = raw_llm.invoke(json_prompt)
                            raw_txt = extract_text(res.content)
                            import json, re
                            m = re.search(r"(\{.*\})", raw_txt, re.DOTALL)
                            if m:
                                return schema.model_validate(json.loads(m.group(1)))
                        except Exception as raw_exc:
                            logger.warning(
                                "Structured-output fallback failed for %s: %s",
                                agent_name,
                                raw_exc,
                            )
                    raise last_err
