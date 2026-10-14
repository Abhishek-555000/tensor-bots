from typing import TypedDict, Optional, List, Dict, Any


class TensorState(TypedDict, total=False):
    """
    The shared state dictionary for Tensor Bots.
    
    # TEACH: total=False allows nodes to return only the subset of keys they modify.
    """
    run_id: str
    user_prompt: str
    briefs: Dict[str, str]
    research: str
    files: List[str]
    iteration: int
