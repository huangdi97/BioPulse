"""Retry policy configuration for LangGraph nodes.

Defines the default retry behaviour: up to 3 attempts with exponential
backoff, retrying only on network-related exceptions.
"""

from langgraph.types import RetryPolicy

default_retry_policy = RetryPolicy(
    max_attempts=3,
    retry_on=[TimeoutError, ConnectionError],
    initial_interval=2.0,
    backoff_factor=2.0,
)
