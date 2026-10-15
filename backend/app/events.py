import time
import functools
from typing import Any, Callable, Dict, Optional
from langgraph.config import get_stream_writer

# Optional external event listener (used by CLI or tests when outside stream context)
_event_listeners = []


def add_event_listener(listener: Callable[[Dict[str, Any]], None]):
    """Register a callback for all emitted events."""
    _event_listeners.append(listener)


def remove_event_listener(listener: Callable[[Dict[str, Any]], None]):
    """Unregister an event listener."""
    if listener in _event_listeners:
        _event_listeners.remove(listener)


def emit(event_type: str, **data) -> Dict[str, Any]:
    """
    Emit a structured real-time event.
    
    # TEACH: The writer sends events to the active `graph.stream(..., stream_mode='custom')`.
    """
    payload = {
        "type": event_type,
        "ts": time.time(),
        **data,
    }
    
    # Send through LangGraph's native stream writer if running within graph stream
    try:
        writer = get_stream_writer()
        if writer:
            writer(payload)
    except Exception:
        # Not currently inside a LangGraph runnable context
        pass
    
    # Also notify any external registered listeners (e.g. CLI fallback)
    for listener in _event_listeners:
        try:
            listener(payload)
        except Exception:
            pass
            
    return payload


def agent_node(agent_name: str):
    """
    Decorator that wraps an agent node function with standard lifecycle events:
    - Emits `agent_started` before execution
    - Emits `agent_done` after successful execution
    - Emits `run_error` and re-raises on uncaught exception
    
    # TEACH: Keeps agent node implementations clean by factoring out boilerplate telemetry.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(state: Dict[str, Any], *args, **kwargs):
            # Display name mapping: manager_final maps to 'manager' in events/UI
            display_agent = "manager" if agent_name == "manager_final" else agent_name
            
            emit("agent_started", agent=display_agent)
            try:
                result = func(state, *args, **kwargs)
                summary_text = f"{display_agent.capitalize()} completed task."
                emit("agent_done", agent=display_agent, summary=summary_text)
                return result
            except Exception as exc:
                error_msg = f"{display_agent.capitalize()} encountered error: {str(exc)}"
                emit("agent_error", agent=display_agent, message=error_msg)
                emit("run_error", message=error_msg)
                raise
        return wrapper
    return decorator
