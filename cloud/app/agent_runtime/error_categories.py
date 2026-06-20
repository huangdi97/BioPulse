"""Error categorization for agent runtime results."""


def categorize_error(status: str) -> str:
    """Map a runtime status string to a high-level error category."""
    mapping = {
        "timeout": "timeout",
        "llm_failed": "llm_failed",
        "llm_limit_exceeded": "llm_failed",
        "budget_exceeded": "budget_exceeded",
        "rate_limited": "rate_limited",
        "blocked": "validation_failed",
        "bulkhead_rejected": "rate_limited",
        "error": "unknown",
        "incomplete": "unknown",
        "degraded": "tool_error",
    }
    return mapping.get(status, "unknown")
