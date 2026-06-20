"""Context usage warning logic — threshold check and streaming notification."""

import logging

from cloud.app.agent_runtime.runtime_llm.config import compress_messages, estimate_token_count
from shared.config import settings as config_settings

logger = logging.getLogger(__name__)


def check_and_warn(messages: list[dict], core) -> list[dict]:
    total = estimate_token_count(messages)
    max_tokens = getattr(config_settings, "max_context_tokens", 128000)
    usage_pct = round(total / max_tokens * 100, 1) if max_tokens > 0 else 0
    streamer = getattr(core, "_streamer", None) if core else None
    trace_id = getattr(core, "_trace_id", "") if core else ""

    if usage_pct >= 95:
        logger.warning("Context usage %d%% >= 95%%, forcing compression (trace=%s)", usage_pct, trace_id)
        if streamer and trace_id:
            streamer.stream(
                trace_id,
                "context.warning",
                {
                    "level": "critical",
                    "usage_pct": usage_pct,
                    "total_tokens": total,
                    "max_tokens": max_tokens,
                    "action": "force_compress",
                },
            )
        return compress_messages(messages)
    if usage_pct >= 80:
        logger.warning("Context usage %d%% >= 80%% threshold (trace=%s)", usage_pct, trace_id)
        if streamer and trace_id:
            streamer.stream(
                trace_id,
                "context.warning",
                {
                    "level": "warning",
                    "usage_pct": usage_pct,
                    "total_tokens": total,
                    "max_tokens": max_tokens,
                    "action": "monitor",
                },
            )

    return compress_messages(messages)
