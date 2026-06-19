"""Trace 查询路由 — 查看单条 trace、按条件搜索、指标汇总。"""
# ruff: noqa: E501

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse, StreamingResponse

if TYPE_CHECKING:
    from cloud.app.agent_runtime.runtime_core import RuntimeCore

from cloud.app.agent_runtime.agent_registry import AgentRegistry
from cloud.app.agent_runtime.evaluator import AgentEvaluator
from cloud.app.agent_runtime.metrics import get_metrics
from cloud.app.agent_runtime.secret_manager import SecretManager
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


_runtime_core: RuntimeCore | None = None


def set_runtime_core(core: "RuntimeCore") -> None:
    global _runtime_core
    _runtime_core = core


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
.filters{margin-bottom:16px;display:flex;gap:12px;align-items:center}
.filters select{padding:8px 12px;border:1px solid #ddd;border-radius:6px;font-size:14px;background:#fff}
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
<div class="nav" style="margin-bottom:16px">
  <a href="/agent/traces/ui">Trace Dashboard</a>
  <a href="/agent/traces/ui/agents">Agent Status</a>
  <a href="/agent/chat/ui">Chat with Agent</a>
</div>
<div class="filters">
  <label>Agent:</label>
  <select id="agent-filter" onchange="loadTraces()">
    <option value="">All Agents</option>
  </select>
</div>
<div id="table-container"><div class="loading">Loading...</div></div>
<script>
async function loadSummary(){try{const r=await fetch('/agent/metrics/summary');const d=await r.json();const data=d.data||{};document.getElementById('total-requests').textContent=data.total_requests??(data.total_runs??'-');document.getElementById('error-rate').textContent=data.error_rate!=null?(data.error_rate+'%'):(data.success_rate!=null?((100-data.success_rate)+'%'):'-');document.getElementById('active-agents').textContent=data.active_agents??'-'}catch(e){document.getElementById('total-requests').textContent='ERR'}}  # noqa: E501
async function loadAgentFilter(){try{const r=await fetch('/agent/traces/ui/agents');const text=await r.text();const sel=document.getElementById('agent-filter');const parser=new DOMParser();const doc=parser.parseFromString(text,'text/html');const rows=doc.querySelectorAll('table tbody tr');rows.forEach(row=>{const cells=row.querySelectorAll('td');if(cells.length>0){const name=cells[0].textContent.trim();if(name){const opt=document.createElement('option');opt.value=name;opt.textContent=name;sel.appendChild(opt)}}})}catch(e){console.error('Failed to load agents',e)}}  # noqa: E501
async function loadTraces(){try{const agent=document.getElementById('agent-filter').value;let url='/agent/traces?page_size=20';if(agent)url+='&agent_name='+encodeURIComponent(agent);const r=await fetch(url);const d=await r.json();const traces=d.data?.items||d.data||[];let html='<table><thead><tr><th>Agent</th><th>Status</th><th>Duration</th><th>Time</th></tr></thead><tbody>';traces.forEach((t,i)=>{const sc=t.status==='success'?'success':t.status==='error'?'error':'warning';html+='<tr onclick=\"toggleDetail('+i+')\"><td>'+(t.agent_name||t.agent||'-')+'</td><td><span class=\"badge '+sc+'\">'+(t.status||'unknown')+'</span></td><td>'+(t.duration_ms||t.total_duration_ms?((t.duration_ms||t.total_duration_ms)+'ms'):'-')+'</td><td>'+(t.created_at||t.started_at||t.timestamp||'-')+'</td></tr>';html+='<tr class=\"detail-row\" id=\"detail-'+i+'\"><td colspan=\"4\"><div class=\"detail-cell\" id=\"detail-content-'+i+'\">Loading...</div></td></tr>'});html+='</tbody></table>';document.getElementById('table-container').innerHTML=html}catch(e){document.getElementById('table-container').innerHTML='Error: '+e.message}}  # noqa: E501
async function toggleDetail(i){const row=document.getElementById('detail-'+i);const active=row.classList.contains('active');document.querySelectorAll('.detail-row.active').forEach(r=>r.classList.remove('active'));if(active)return;row.classList.add('active');const el=document.getElementById('detail-content-'+i);if(el.dataset.loaded)return;el.dataset.loaded='true';try{const agent=document.getElementById('agent-filter').value;let url='/agent/traces?page_size=20';if(agent)url+='&agent_name='+encodeURIComponent(agent);const t=await(await fetch(url)).json();const items=t.data?.items||t.data||[];const item=items[i];if(!item){el.innerHTML='No data';return}const tr=await(await fetch('/agent/traces/'+(item.trace_id||item.id))).json();const trace=tr.data||tr;let s='';(trace.steps||trace.execution_steps||[]).forEach(st=>{s+='<div class=\"step '+(st.status==='success'?'success':'error')+'\">'+ (st.tool||st.action||st.name||'step')+'</div>'});el.innerHTML=s||'No step details'}catch(e){el.innerHTML='Error loading'}}  # noqa: E501
loadSummary();loadAgentFilter();loadTraces();
</script>
</body>
</html>""")


@router.get("/traces/ui/agents", tags=["Agent Traces"], include_in_schema=False)
def agent_status_ui(user=Depends(require_scope("visit"))):
    """Agent 状态概览 HTML 页面 — 列出所有注册 Agent 的名称/角色/状态/最后活跃时间。"""
    from fastapi.responses import HTMLResponse

    agents = AgentRegistry.list()
    tracer = _get_tracer()

    rows_html = ""
    for agent in agents:
        _ = agent.identity.key  # noqa: F841
        name = agent.identity.name
        role = agent.identity.role
        status = "online"
        last_active = "-"
        last_result = "-"
        success_rate = "-"

        traces = tracer.list_traces(agent_name=name, page=1, page_size=5)
        items = traces.get("items", [])
        if items:
            last_active = items[0].get("started_at", items[0].get("created_at", "-"))
            last_result = items[0].get("status", "-")

        all_traces = tracer.list_traces(agent_name=name, page=1, page_size=1000)
        all_items = all_traces.get("items", [])
        if all_items:
            success_count = sum(1 for t in all_items if t.get("status") == "success")
            success_rate = f"{round(success_count / len(all_items) * 100, 1)}%"

        rows_html += f"""<tr>
<td>{name}</td>
<td>{role}</td>
<td><span class="badge {"success" if status == "online" else "warning"}">{status}</span></td>
<td>{last_active}</td>
<td><span class="badge {"success" if last_result == "success" else ("error" if last_result == "error" else "warning")}">{last_result}</span></td>
<td>{success_rate}</td>
</tr>"""

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Agent Status Overview</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f7fa;color:#333;padding:24px}}
h1{{font-size:24px;margin-bottom:20px;color:#1a1a2e}}
.nav{{margin-bottom:16px;display:flex;gap:12px}}
.nav a{{color:#4a6cf7;text-decoration:none;font-size:14px;padding:6px 12px;border-radius:6px;background:#fff;border:1px solid #e0e0e0}}
.nav a:hover{{background:#f0f2ff}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08)}}
th{{background:#f0f2f5;text-align:left;padding:12px 16px;font-size:13px;font-weight:600;color:#666}}
td{{padding:12px 16px;border-top:1px solid #eee;font-size:14px}}
.badge{{display:inline-block;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:600}}
.badge.success{{background:#d4edda;color:#155724}} .badge.error{{background:#f8d7da;color:#721c24}}
.badge.warning{{background:#fff3cd;color:#856404}}
</style>
</head>
<body>
<h1>Agent Status Overview</h1>
<div class="nav">
  <a href="/agent/traces/ui">Trace Dashboard</a>
  <a href="/agent/traces/ui/agents">Agent Status</a>
  <a href="/agent/chat/ui">Chat with Agent</a>
</div>
<table>
<thead><tr><th>Name</th><th>Role</th><th>Status</th><th>Last Active</th><th>Last Result</th><th>Success Rate</th></tr></thead>
<tbody>{rows_html}</tbody>
</table>
</body>
</html>""")


@router.get(
    "/traces/{trace_id}",
    tags=["Agent Traces"],
    operation_id="agents_get_trace",
    summary="获取单条trace详情",
    response_description="返回trace详情",
)
def get_trace(trace_id: str, user=Depends(require_scope("visit"))):
    tracer = _get_tracer()
    trace = tracer.get_trace(trace_id)
    if trace is None:
        from fastapi import HTTPException
        from starlette import status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found")
    return success(data=trace)


@router.get("/traces", tags=["Agent Traces"], operation_id="agents_list_traces", summary="列出Agent执行记录", response_description="返回trace列表")
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


@router.get(
    "/metrics/summary",
    tags=["Agent Traces"],
    operation_id="agents_metrics_summary",
    summary="获取指标汇总",
    response_description="返回指标汇总",
)
def metrics_summary(user=Depends(require_scope("visit"))):
    tracer = _get_tracer()
    return success(data=tracer.get_metrics_summary())


@router.get(
    "/eval/dashboard",
    tags=["Agent Traces"],
    operation_id="agents_eval_dashboard",
    summary="获取Agent评估面板",
    response_description="返回评估数据",
)
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

_secret_manager: SecretManager | None = None


def _get_secret_manager() -> SecretManager:
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = SecretManager()
    return _secret_manager


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


@router.get("/config/secrets", tags=["Agent Traces"], operation_id="config_list_secrets", summary="列出所有密钥状态", include_in_schema=False)
def list_secrets(user=Depends(require_scope("admin"))):
    from shared.base import success

    sm = _get_secret_manager()
    return success(data=sm.export_keys())


@router.post("/config/secrets/{key_name}", tags=["Agent Traces"], operation_id="config_set_secret", summary="设置密钥值", include_in_schema=False)
def set_secret(key_name: str, body: dict, user=Depends(require_scope("admin"))):
    from fastapi import HTTPException
    from starlette import status as http_status

    from shared.base import success as ok

    value = body.get("value", "")
    if not value:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="value is required")
    sm = _get_secret_manager()
    sm.set(key_name, value)
    return ok(data={"key_name": key_name, "updated": True})


@router.delete("/config/secrets/{key_name}", tags=["Agent Traces"], operation_id="config_delete_secret", summary="删除密钥", include_in_schema=False)
def delete_secret(key_name: str, user=Depends(require_scope("admin"))):
    from shared.base import success

    sm = _get_secret_manager()
    sm.delete(key_name)
    return success(data={"key_name": key_name, "deleted": True})


@router.get(
    "/checkpoints/recoverable",
    tags=["Agent Traces"],
    operation_id="checkpoints_list_recoverable",
    summary="列出可恢复的checkpoint",
    include_in_schema=False,
)  # noqa: E501
def list_recoverable(user=Depends(require_scope("admin"))):
    import sqlite3

    from cloud.app.agent_runtime.state_snapshot import recover as recover_fn
    from cloud.app.database import DB_PATH

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        snapshots = recover_fn(conn)
        result = []
        for snap in snapshots:
            state = snap.get("state", {})
            result.append(
                {
                    "trace_id": snap.get("trace_id", ""),
                    "agent_key": state.get("agent_key", ""),
                    "goal": state.get("goal", ""),
                    "step": snap.get("step", 0),
                    "created_at": snap.get("created_at", ""),
                }
            )
        return success(data=result)
    finally:
        conn.close()


@router.post(
    "/checkpoints/{trace_id}/resume",
    tags=["Agent Traces"],
    operation_id="checkpoints_resume",
    summary="恢复执行中断的checkpoint",
    include_in_schema=False,
)  # noqa: E501
def resume_checkpoint(trace_id: str, body: dict, user=Depends(require_scope("admin"))):
    import sqlite3

    from cloud.app.agent_runtime.state_snapshot import load_latest_snapshot
    from cloud.app.database import DB_PATH

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        snap = load_latest_snapshot(conn, trace_id)
        if not snap:
            from fastapi import HTTPException
            from starlette import status

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checkpoint not found")
        state = snap.get("state", {})
        agent_key = state.get("agent_key", "")
        goal = state.get("goal", "")
        if not agent_key or not goal:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid checkpoint state")
        from cloud.app.agent_runtime.runtime_core import RuntimeCore

        runtime = RuntimeCore(conn, conn, body.get("auth_header", ""))
        result = runtime.execute(goal, agent_key, state.get("context", {}))
        return success(data=result.model_dump())
    finally:
        conn.close()


@router.get("/slo/alerts", tags=["Agent Traces"], operation_id="slo_list_alerts", summary="获取SLO告警记录", include_in_schema=False)
def slo_alerts(
    agent_name: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user=Depends(require_scope("visit")),
):
    from cloud.app.agent_runtime.slo_monitor import get_breach_summary

    summary = get_breach_summary(hours=24)
    if agent_name:
        summary["breaches"] = [b for b in summary["breaches"] if b.get("agent_name") == agent_name]
        summary["total_breaches"] = len(summary["breaches"])
    return success(data=summary)


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
