from typing import TypedDict, Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AgentBriefs(BaseModel):
    """Structured task briefs dispatched by the Project Manager."""
    researcher: str = Field(
        description="1-3 sentence brief for Researcher: key constraints, architecture considerations, best practices"
    )
    planner: str = Field(
        description="1-3 sentence brief for Planner: file list (<= 4 files), components, structure, and design decisions"
    )
    developer: str = Field(
        description="1-3 sentence brief for Developer: implementation guidance, simplicity rules, coding standards"
    )
    reviewer: str = Field(
        description="1-3 sentence brief for Reviewer: verification criteria, completeness checks, and quality standards"
    )


class TensorState(TypedDict, total=False):
    """
    The shared state dictionary for Tensor Bots.
    
    # TEACH: total=False allows nodes to return only the subset of keys they modify.
    # When researcher and planner execute concurrently, their returned keys do not clash.
    """
    run_id: str
    user_prompt: str
    briefs: Dict[str, str]       # Serialized AgentBriefs
    research: str                # Markdown output from Researcher
    plan: str                    # Markdown plan & file breakdown from Planner
    files: List[str]             # List of files created
    iteration: int               # Cycle counter
