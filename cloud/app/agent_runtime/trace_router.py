"""Trace 查询路由 — 查看单条 trace、按条件搜索、指标汇总。"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path

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


BIOPULSE_AUDIT_LOG = os.environ.get("BIOPULSE_AUDIT_LOG", "data/biopulse_audit.log")


def _get_audit_logger() -> logging.Logger:
    logger = logging.getLogger("biopulse-audit")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        log_dir = os.path.dirname(BIOPULSE_AUDIT_LOG)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        handler = logging.FileHandler(BIOPULSE_AUDIT_LOG, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.propagate = False
    return logger


def log_agent_decision(
    agent_name: str,
    input_summary: str,
    decisions: list,
    risk_level: str,
    approval_status: str,
    human_reviewer: str = "",
) -> None:
    record = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "agent_name": agent_name,
        "input_summary": input_summary,
        "decisions": decisions,
        "risk_level": risk_level,
        "approval_status": approval_status,
        "human_reviewer": human_reviewer,
    }
    _get_audit_logger().info(json.dumps(record, ensure_ascii=False))

    if risk_level == "high":
        auto_record = {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "agent_name": agent_name,
            "input_summary": input_summary,
            "decisions": decisions,
            "risk_level": risk_level,
            "approval_status": approval_status,
            "human_reviewer": human_reviewer,
            "auto_audit": True,
            "auto_audit_reason": "high_risk",
        }
        _get_audit_logger().info(json.dumps(auto_record, ensure_ascii=False))


def get_agent_decisions(
    agent_name: str | None = None,
    risk_level: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
) -> list[dict]:
    log_file = Path(BIOPULSE_AUDIT_LOG)
    if not log_file.exists():
        return []

    records: list[dict] = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if agent_name and record.get("agent_name") != agent_name:
                continue
            if risk_level and record.get("risk_level") != risk_level:
                continue
            if date_from and record.get("timestamp", "") < date_from:
                continue
            if date_to and record.get("timestamp", "") > date_to:
                continue
            records.append(record)

    records.reverse()
    return records[:limit]


def auto_audit_decision(
    agent_name: str,
    input_summary: str,
    decisions: list,
    risk_level: str,
) -> None:
    log_agent_decision(
        agent_name=agent_name,
        input_summary=input_summary,
        decisions=decisions,
        risk_level=risk_level,
        approval_status="auto_audited",
        human_reviewer="system",
    )
