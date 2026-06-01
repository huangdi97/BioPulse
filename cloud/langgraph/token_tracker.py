"""Token usage tracking and cost estimation for LangGraph LLM calls.

Logs prompt/completion token counts per LLM call and estimates cost
based on DeepSeek pricing (¥0.5/M input tokens, ¥2.0/M output tokens).
"""

import sqlite3
import os
from datetime import datetime, timezone
from typing import Any
from langchain_core.callbacks import BaseCallbackHandler

DEEPSEEK_PRICES = {"input": 0.5, "output": 2.0}

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "token_usage.db",
)


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Estimate the cost of an LLM call based on token counts.

    Uses DeepSeek pricing: ¥0.5 per million input tokens, ¥2.0 per million output tokens.

    Args:
        model: Model name (used for future per-model pricing).
        prompt_tokens: Number of input/prompt tokens.
        completion_tokens: Number of output/completion tokens.

    Returns:
        Estimated cost in CNY, rounded to 6 decimal places.
    """
    input_cost = (prompt_tokens / 1_000_000) * DEEPSEEK_PRICES["input"]
    output_cost = (completion_tokens / 1_000_000) * DEEPSEEK_PRICES["output"]
    return round(input_cost + output_cost, 6)


class TokenTracker(BaseCallbackHandler):
    """LangChain callback that logs LLM token usage to a local SQLite database.

    Attach this handler to a LangGraph graph to automatically record
    token consumption and estimated cost for every LLM call.

    Usage:
        tracker = TokenTracker()
        graph = builder.compile(callbacks=[tracker])
    """

    def __init__(self, db_path: str | None = None):
        """Initialize the tracker and ensure the token_usage_log table exists.

        Args:
            db_path: Path to the SQLite database file.
                     Defaults to data/token_usage.db.
        """
        path = db_path or DB_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.conn = sqlite3.connect(path)
        self._ensure_table()
        self._current_call_id: str | None = None

    def _ensure_table(self):
        """Create the token_usage_log table if it does not exist."""
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS token_usage_log ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "call_id TEXT NOT NULL, "
            "model TEXT NOT NULL DEFAULT '', "
            "prompt_tokens INTEGER NOT NULL DEFAULT 0, "
            "completion_tokens INTEGER NOT NULL DEFAULT 0, "
            "estimated_cost REAL NOT NULL DEFAULT 0.0, "
            "timestamp TEXT NOT NULL"
            ")"
        )
        self.conn.commit()

    def on_llm_start(
        self, serialized: dict, prompts: list[str], **kwargs: Any
    ) -> Any:
        """Record the start of an LLM call with a unique call_id."""
        self._current_call_id = kwargs.get("run_id", str(datetime.now(timezone.utc).timestamp()))

    def on_llm_end(self, response, **kwargs: Any) -> Any:
        """Record the end of an LLM call, logging token usage to the database."""
        if not self._current_call_id:
            return
        llm_output = getattr(response, "llm_output", None) or {}
        token_usage = llm_output.get("token_usage", {})
        prompt_tokens = token_usage.get("prompt_tokens", 0)
        completion_tokens = token_usage.get("completion_tokens", 0)
        model = llm_output.get("model", "")
        cost = estimate_cost(model, prompt_tokens, completion_tokens)
        self.conn.execute(
            "INSERT INTO token_usage_log (call_id, model, prompt_tokens, completion_tokens, estimated_cost, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                self._current_call_id,
                model,
                prompt_tokens,
                completion_tokens,
                cost,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()
        self._current_call_id = None
