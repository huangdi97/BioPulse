"""Trace 查询路由 — 查看单条 trace、按条件搜索、指标汇总。"""

import sqlite3

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse, StreamingResponse

from cloud.app.agent_runtime.evaluator import AgentEvaluator
from cloud.app.agent_runtime.metrics import get_metrics
from cloud.app.agent_runtime.streamer import AgentStreamer
from cloud.app.agent_runtime.tracer import AgentTracer
from cloud.app.database import DB_PATH
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/agent", tags=["Agent Traces"])

_streamer: AgentStreamer | None = None


def get_streamer() -> AgentStreamer:
    """get streamer."""
    global _streamer
    if _streamer is None:
        _streamer = AgentStreamer()
    return _streamer


def _get_tracer() -> AgentTracer:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return AgentTracer(conn)


@router.get("/traces/{trace_id}", tags=["Agent Traces"])
def get_trace(trace_id: str, user=Depends(require_scope("visit"))):
    tracer = _get_tracer()
    trace = tracer.get_trace(trace_id)
    if trace is None:
        from fastapi import HTTPException
        from starlette import status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found")
    return success(data=trace)


@router.get("/traces", tags=["Agent Traces"])
def list_traces(
    agent_name: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user=Depends(require_scope("visit")),
):
    tracer = _get_tracer()
    result = tracer.list_traces(agent_name=agent_name, page=page, page_size=page_size)
    return success(data=result)


@router.get("/metrics", tags=["Agent Traces"], response_class=PlainTextResponse)
def prometheus_metrics():
    return PlainTextResponse(get_metrics())


@router.get("/metrics/summary", tags=["Agent Traces"])
def metrics_summary(user=Depends(require_scope("visit"))):
    tracer = _get_tracer()
    return success(data=tracer.get_metrics_summary())


@router.get("/eval/dashboard", tags=["Agent Traces"])
def eval_dashboard(user=Depends(require_scope("visit"))):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        evaluator = AgentEvaluator(conn)
        return success(data=evaluator.get_dashboard())
    finally:
        conn.close()


@router.get("/traces/{trace_id}/stream", tags=["Agent Traces"])
def stream_trace(trace_id: str, user=Depends(require_scope("visit"))):
    streamer = get_streamer()
    return StreamingResponse(
        streamer.get_stream(trace_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
