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


@router.get("/traces/ui", tags=["Agent Traces"], include_in_schema=False)
def trace_dashboard_ui(user=Depends(require_scope("visit"))):
    """Agent Trace Dashboard HTML UI."""
    from fastapi.responses import HTMLResponse
    return HTMLResponse("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Agent Trace Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f7fa;color:#333;padding:24px}
h1{font-size:24px;margin-bottom:20px;color:#1a1a2e}
.cards{display:flex;gap:16px;margin-bottom:24px}
.card{flex:1;background:#fff;border-radius:10px;padding:20px;box-shadow:0 1px 4px rgba(0,0,0,.08)}
.card .label{font-size:13px;color:#888;margin-bottom:6px}
.card .value{font-size:28px;font-weight:700;color:#1a1a2e}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08)}
th{background:#f0f2f5;text-align:left;padding:12px 16px;font-size:13px;font-weight:600;color:#666}
td{padding:12px 16px;border-top:1px solid #eee;font-size:14px}
tr{cursor:pointer;transition:background .15s}
tr:hover{background:#f8f9ff}
.detail-row{display:none}
.detail-row.active{display:table-row}
.detail-cell{padding:16px 24px;background:#fafbff;border-top:2px solid #e8eaff}
.step{border-left:3px solid;padding:8px 12px;margin:6px 0;background:#fff;border-radius:4px;font-size:13px}
.step.success{border-color:#2ecc71} .step.error{border-color:#e74c3c} .step.warning{border-color:#f39c12}
.badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:600}
.badge.success{background:#d4edda;color:#155724} .badge.error{background:#f8d7da;color:#721c24}
.badge.warning{background:#fff3cd;color:#856404}
.loading{text-align:center;padding:60px;color:#999;font-size:16px}
</style>
</head>
<body>
<h1>Agent Trace Dashboard</h1>
<div class="cards" id="cards">
  <div class="card"><div class="label">Total Requests</div><div class="value" id="total-requests">-</div></div>
  <div class="card"><div class="label">Error Rate</div><div class="value" id="error-rate">-</div></div>
  <div class="card"><div class="label">Active Agents</div><div class="value" id="active-agents">-</div></div>
</div>
<div id="table-container"><div class="loading">Loading...</div></div>
<script>
async function loadSummary(){try{const r=await fetch('/agent/metrics/summary');const d=await r.json();const data=d.data||{};document.getElementById('total-requests').textContent=data.total_requests??'-';document.getElementById('error-rate').textContent=data.error_rate!=null?(data.error_rate+'%'):'-';document.getElementById('active-agents').textContent=data.active_agents??'-'}catch(e){document.getElementById('total-requests').textContent='ERR'}}
async function loadTraces(){try{const r=await fetch('/agent/traces?page_size=20');const d=await r.json();const traces=d.data?.items||d.data||[];let html='<table><thead><tr><th>Agent</th><th>Status</th><th>Duration</th><th>Time</th></tr></thead><tbody>';traces.forEach((t,i)=>{const sc=t.status==='success'?'success':t.status==='error'?'error':'warning';html+='<tr onclick=\"toggleDetail('+i+')\"><td>'+(t.agent_name||t.agent||'-')+'</td><td><span class=\"badge '+sc+'\">'+(t.status||'unknown')+'</span></td><td>'+(t.duration_ms?t.duration_ms+'ms':'-')+'</td><td>'+(t.created_at||t.timestamp||'-')+'</td></tr>';html+='<tr class=\"detail-row\" id=\"detail-'+i+'\"><td colspan=\"4\"><div class=\"detail-cell\" id=\"detail-content-'+i+'\">Loading...</div></td></tr>'});html+='</tbody></table>';document.getElementById('table-container').innerHTML=html}catch(e){document.getElementById('table-container').innerHTML='Error: '+e.message}}
async function toggleDetail(i){const row=document.getElementById('detail-'+i);const active=row.classList.contains('active');document.querySelectorAll('.detail-row.active').forEach(r=>r.classList.remove('active'));if(active)return;row.classList.add('active');const el=document.getElementById('detail-content-'+i);if(el.dataset.loaded)return;el.dataset.loaded='true';try{const t=await(await fetch('/agent/traces?page_size=20')).json();const items=t.data?.items||t.data||[];const item=items[i];if(!item){el.innerHTML='No data';return}const tr=await(await fetch('/agent/traces/'+(item.trace_id||item.id))).json();const trace=tr.data||tr;let s='';(trace.steps||trace.execution_steps||[]).forEach(st=>{s+='<div class=\"step '+(st.status==='success'?'success':'error')+'\">'+ (st.tool||st.action||st.name||'step')+'</div>'});el.innerHTML=s||'No step details'}catch(e){el.innerHTML='Error loading'}}
loadSummary();loadTraces();
</script>
</body>
</html>""")


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
