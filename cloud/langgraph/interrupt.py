"""Human-in-the-loop interrupt/resume node for LangGraph.

When needs_review is True, the graph pauses execution and waits for
an external approval decision. The caller can resume with Command(resume=...).
"""

from langgraph.types import interrupt


def human_review_node(state: dict) -> dict:
    """Pause graph execution for human review when needs_review is True.

    When called, this node raises an interrupt with the current state.
    The caller must resume with Command(resume={'decision': 'approve'|'reject'}).

    Args:
        state: The current AgentState dict, must contain 'needs_review' bool.

    Returns:
        The (possibly modified) state dict. If rejected, next_agent is set
        to 'rejected' so downstream nodes can handle it.
    """
    if state.get("needs_review", False):
        review = interrupt({"question": "Approve or reject this step?", "state": state})
        if isinstance(review, dict) and review.get("decision") == "reject":
            return {**state, "next_agent": "rejected"}
    return state
