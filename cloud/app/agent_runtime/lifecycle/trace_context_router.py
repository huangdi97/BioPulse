"""Trace 上下文路由 — 获取上下文用量和截取对话。"""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from cloud.app.database import DB_PATH
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/agent", tags=["Agent Traces"])

_DEFAULT_MAX_CONTEXT_TOKENS = 128000


@router.get(
    "/runtime/{trace_id}/context",
    tags=["Agent Traces"],
    operation_id="runtime_get_context",
    summary="获取指定 trace 的上下文用量信息",
    include_in_schema=False,
)
def get_context(trace_id: str, user=Depends(require_scope("visit"))):
    """Get context usage info (token count, usage %) for a given trace."""
    from cloud.app.agent_runtime.runtime_llm.config import estimate_token_count

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        from cloud.app.agent_runtime.memory.state_snapshot import load_latest_snapshot

        snap = load_latest_snapshot(conn, trace_id)
        if not snap:
            from fastapi import HTTPException
            from starlette import status

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found")
        state = snap.get("state", {})
        messages = state.get("messages", [])
        message_count = len(messages)
        total_tokens = estimate_token_count(messages)
        max_tokens = _DEFAULT_MAX_CONTEXT_TOKENS
        usage_pct = round(total_tokens / max_tokens * 100, 2) if max_tokens > 0 else 0
        return success(
            data={
                "trace_id": trace_id,
                "total_tokens": total_tokens,
                "max_tokens": max_tokens,
                "usage_pct": usage_pct,
                "message_count": message_count,
            }
        )
    finally:
        conn.close()


class PruneContextRequest(BaseModel):
    """Request model for context pruning, specifying how many rounds to keep."""

    keep_rounds: int = Field(default=10, ge=1)


@router.post(
    "/runtime/{trace_id}/context/prune",
    tags=["Agent Traces"],
    operation_id="runtime_prune_context",
    summary="截取指定 trace 的最后 N 轮对话",
    include_in_schema=False,
)
def prune_context(trace_id: str, body: PruneContextRequest, user=Depends(require_scope("admin"))):
    """Prune conversation history for a trace, keeping only the last N rounds."""
    from cloud.app.agent_runtime.runtime_llm.config import estimate_token_count

    keep_rounds = body.keep_rounds

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        from cloud.app.agent_runtime.memory.state_snapshot import load_latest_snapshot, save_snapshot

        snap = load_latest_snapshot(conn, trace_id)
        if not snap:
            from fastapi import HTTPException
            from starlette import status

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found")
        state = snap.get("state", {})
        messages = state.get("messages", [])
        system_msgs = [m for m in messages if m.get("role") == "system"]
        non_system = [m for m in messages if m.get("role") != "system"]
        kept = non_system[-(keep_rounds * 2) :]
        pruned_count = len(non_system) - len(kept)
        state["messages"] = system_msgs + kept
        save_snapshot(conn, trace_id, snap["step"], state)
        after_tokens = estimate_token_count(state["messages"])
        return success(
            data={
                "trace_id": trace_id,
                "pruned_messages": pruned_count,
                "remaining_messages": len(state["messages"]),
                "remaining_tokens": after_tokens,
            }
        )
    finally:
        conn.close()
