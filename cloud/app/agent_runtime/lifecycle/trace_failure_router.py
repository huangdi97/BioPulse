"""Trace 失败统计路由 — 按 error_category 分组的失败统计。"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query

from cloud.app.database import DB_PATH
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/agent", tags=["Agent Traces"])


@router.get(
    "/traces/failure-stats",
    tags=["Agent Traces"],
    operation_id="agents_failure_stats",
    summary="按 error_category 分组的失败统计",
    include_in_schema=False,
)
def failure_stats(days: int = Query(7, ge=1, le=90), user=Depends(require_scope("visit"))):
    """Return failure statistics grouped by error_category over the past N days."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        rows = conn.execute(
            "SELECT output_data FROM agent_traces WHERE status != 'success' AND started_at >= ?",
            (cutoff,),
        ).fetchall()
        categories: dict[str, int] = {}
        for row in rows:
            try:
                output = json.loads(row["output_data"]) if row["output_data"] else {}
            except (json.JSONDecodeError, TypeError):
                output = {}
            metadata = output.get("metadata", {}) or {}
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            error_cat = metadata.get("error_category", "unknown")
            categories[error_cat] = categories.get(error_cat, 0) + 1
        return success(
            data={
                "period_days": days,
                "total_failures": len(rows),
                "by_category": categories,
            }
        )
    finally:
        conn.close()
