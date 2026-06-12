"""拜访历史收集来源。"""

from __future__ import annotations

import sqlite3
from typing import Any


def query_visit_history(db: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    """查询代表与 HCP 的历史拜访。

    Args:
        db: 数据库连接。
        args: 包含 rep_id、hcp_id 与 limit 的参数。

    Returns:
        拜访历史摘要与记录列表。
    """
    hcp_id = str(args.get("hcp_id", ""))
    limit = int(args.get("limit", 5))
    rows = safe_visit_rows(db, hcp_id, limit)
    return {
        "hcp_id": hcp_id,
        "rep_id": args.get("rep_id"),
        "visit_count": len(rows),
        "recent_visits": rows,
        "summary": summarize_visits(rows),
    }


def safe_visit_rows(db: sqlite3.Connection, hcp_id: str, limit: int) -> list[dict[str, Any]]:
    """安全读取拜访记录。

    Args:
        db: 数据库连接。
        hcp_id: HCP ID。
        limit: 最大返回条数。

    Returns:
        拜访记录字典列表。
    """
    try:
        rows = db.execute(
            "SELECT * FROM visits WHERE CAST(hcp_id AS TEXT)=? ORDER BY created_at DESC LIMIT ?",
            (hcp_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    except Exception:
        logger.warning("Visit collector异常", exc_info=True)
        return []


def summarize_visits(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """生成拜访历史摘要。

    Args:
        rows: 拜访记录列表。

    Returns:
        拜访频次、最近内容与拜访类型摘要。
    """
    visit_types = sorted({str(row.get("visit_type", "")) for row in rows if row.get("visit_type")})
    latest = rows[0] if rows else {}
    return {
        "frequency_signal": "high" if len(rows) >= 3 else "low" if not rows else "medium",
        "latest_content": latest.get("content", ""),
        "visit_types": visit_types,
    }
