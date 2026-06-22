"""成本查询路由 — 每日成本、按Agent排行、按模型占比。"""

import sqlite3

from fastapi import APIRouter, Depends, Query

from cloud.app.agent_runtime.safety.cost_governor import CostGovernor
from cloud.app.database import DB_PATH
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/agent/costs", tags=["Agent Costs"])


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/daily", tags=["Agent Costs"])
def daily_costs(
    start: str = Query("2026-06-01"),
    end: str = Query("2026-06-10"),
    user=Depends(require_scope("visit")),
):
    db = _get_db()
    try:
        governor = CostGovernor()
        data = governor.get_daily_costs(db, start, end)
        return success(data=data)
    finally:
        db.close()


@router.get("/by-agent", tags=["Agent Costs"])
def costs_by_agent(user=Depends(require_scope("visit"))):
    db = _get_db()
    try:
        governor = CostGovernor()
        data = governor.get_costs_by_agent(db)
        return success(data=data)
    finally:
        db.close()


@router.get("/by-model", tags=["Agent Costs"])
def costs_by_model(user=Depends(require_scope("visit"))):
    db = _get_db()
    try:
        governor = CostGovernor()
        data = governor.get_costs_by_model(db)
        return success(data=data)
    finally:
        db.close()


@router.get("/summary", tags=["Agent Costs"])
def cost_summary(user=Depends(require_scope("visit"))):
    """返回所有 Agent 的成本汇总。"""
    db = _get_db()
    try:
        governor = CostGovernor()
        by_agent = governor.get_costs_by_agent(db)
        by_model = governor.get_costs_by_model(db)
        total_cost = sum(r["total_cost"] for r in by_agent)
        total_tokens = sum(r["total_input"] + r["total_output"] for r in by_agent)
        return success(
            data={
                "total_cost": round(total_cost, 4),
                "total_tokens": total_tokens,
                "agents": by_agent,
                "models": by_model,
            }
        )
    finally:
        db.close()


@router.get("/daily-trend", tags=["Agent Costs"])
def daily_trend(
    days: int = Query(7, ge=1, le=90),
    user=Depends(require_scope("visit")),
):
    """返回最近 N 天的每日成本趋势。"""
    from datetime import datetime, timedelta

    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    db = _get_db()
    try:
        governor = CostGovernor()
        data = governor.get_daily_costs(db, start, end)
        return success(data=data)
    finally:
        db.close()
