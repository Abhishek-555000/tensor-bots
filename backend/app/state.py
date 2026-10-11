"""
LangGraph Idea: Graph State (Channels & Schemas)
------------------------------------------------
In LangGraph, 'State' is the single source of truth passed across all nodes in
the graph. Nodes read from this dictionary and return partial updates to merge.
Because parallel branches ('researcher' and 'planner') write to distinct keys
('research' and 'plan'), no conflict reducers are required!
# TEACH: TypedDict defines the shape; Pydantic models validate structured outputs.
"""

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


class ReviewVerdict(BaseModel):
    """Structured evaluation returned by the Reviewer agent."""
    approved: bool = Field(
        description="True if the implementation matches the plan and has no critical bugs, False if revisions are needed"
    )
    issues: List[str] = Field(
        default_factory=list,
        description="Specific actionable issues or missing elements if changes are requested"
    )
    summary: str = Field(
        description="One-sentence verdict summary"
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
    files: List[str]             # List of file paths created in workspace/<run_id>/
    review: Dict[str, Any]       # Serialized ReviewVerdict
    iteration: int               # Review cycle counter (1-based)
    final_summary: str           # Final wrap-up summary from Manager
