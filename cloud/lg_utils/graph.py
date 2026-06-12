"""LangGraph graph definitions for testing and production use.

Provides ready-to-use graph builders for:
- get_test_graph: basic A→B pipeline with MemorySaver
- get_persistent_graph: A→B pipeline with SqliteSaver persistence
- get_retry_graph: A(fallible)→B pipeline with retry policy
- get_interrupt_graph: A→review→B pipeline with human-in-the-loop
"""

import random
from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph

from cloud.lg_utils.checkpointer import get_sqlite_checkpointer
from cloud.lg_utils.interrupt import human_review_node
from cloud.lg_utils.retry import default_retry_policy


class AgentState(TypedDict):
    """Shared state passed between LangGraph nodes.

    Attributes:
        messages: List of message strings accumulated during execution.
        next_agent: Identifies the next agent or node to execute.
        metadata: Arbitrary metadata dict for cross-node context.
        needs_review: Flag indicating whether human review is required.
    """

    messages: list
    next_agent: str
    metadata: dict
    needs_review: bool


def node_a(state: AgentState) -> AgentState:
    """Simple passthrough node that appends 'processed_by_A' to messages."""
    return {
        "messages": state["messages"] + ["processed_by_A"],
        "next_agent": state.get("next_agent", ""),
        "metadata": state.get("metadata", {}),
        "needs_review": state.get("needs_review", False),
    }


def node_b(state: AgentState) -> AgentState:
    """Simple passthrough node that appends 'processed_by_B' to messages."""
    return {
        "messages": state["messages"] + ["processed_by_B"],
        "next_agent": state.get("next_agent", ""),
        "metadata": state.get("metadata", {}),
        "needs_review": state.get("needs_review", False),
    }


def node_a_fallible(state: AgentState) -> AgentState:
    """Node with 50% simulated failure rate to test retry policy.

    Raises ConnectionError half the time to trigger automatic retries.
    """
    if random.random() < 0.5:
        raise ConnectionError("Simulated network failure in node A")
    return {
        "messages": state["messages"] + ["processed_by_A_after_retry"],
        "next_agent": state.get("next_agent", ""),
        "metadata": state.get("metadata", {}),
        "needs_review": state.get("needs_review", False),
    }


def get_test_graph():
    """Build a basic A→B pipeline with in-memory checkpointing.

    Useful for quick smoke tests where persistence is not needed.
    """
    builder = StateGraph(AgentState).add_node("A", node_a).add_node("B", node_b).add_edge("A", "B").set_entry_point("A").set_finish_point("B")
    graph = builder.compile(checkpointer=MemorySaver())
    return graph


def get_persistent_graph():
    """Build an A→B pipeline with SqliteSaver checkpoint persistence.

    Graph state survives process restarts. Suitable for production use.
    """
    builder = StateGraph(AgentState).add_node("A", node_a).add_node("B", node_b).add_edge("A", "B").set_entry_point("A").set_finish_point("B")
    graph = builder.compile(checkpointer=get_sqlite_checkpointer())
    return graph


def get_retry_graph():
    """Build an A→B pipeline where node A has automatic retry on failure.

    Node A has a 50% chance of failing with ConnectionError.
    The retry policy handles up to 3 attempts with exponential backoff.
    """
    builder = (
        StateGraph(AgentState)
        .add_node("A", node_a_fallible, retry_policy=default_retry_policy)
        .add_node("B", node_b)
        .add_edge("A", "B")
        .set_entry_point("A")
        .set_finish_point("B")
    )
    graph = builder.compile()
    return graph


def get_interrupt_graph():
    """Build an A→review→B pipeline with human-in-the-loop interrupt.

    The review node checks needs_review flag. If True, the graph pauses
    and waits for external approval via Command(resume=...).
    """
    builder = (
        StateGraph(AgentState)
        .add_node("A", node_a)
        .add_node("review", human_review_node)
        .add_node("B", node_b)
        .add_edge("A", "review")
        .add_edge("review", "B")
        .set_entry_point("A")
        .set_finish_point("B")
    )
    graph = builder.compile(checkpointer=MemorySaver())
    return graph
