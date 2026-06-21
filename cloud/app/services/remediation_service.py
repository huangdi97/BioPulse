"""整改工单服务 — 红灯事件→整改工单创建→9状态机生命周期管理。"""

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

logger = logging.getLogger(__name__)


class OrderStatus(str, Enum):
    discovered = "discovered"
    confirmed = "confirmed"
    analyzing = "analyzing"
    assigned = "assigned"
    remediating = "remediating"
    reviewing = "reviewing"
    scored = "scored"
    closed = "closed"
    archived = "archived"


# 合法状态转换：只允许按顺序前进，不可跳级或倒退
_VALID_TRANSITIONS: dict[OrderStatus, list[OrderStatus]] = {
    OrderStatus.discovered: [OrderStatus.confirmed],
    OrderStatus.confirmed: [OrderStatus.analyzing],
    OrderStatus.analyzing: [OrderStatus.assigned],
    OrderStatus.assigned: [OrderStatus.remediating],
    OrderStatus.remediating: [OrderStatus.reviewing],
    OrderStatus.reviewing: [OrderStatus.scored],
    OrderStatus.scored: [OrderStatus.closed, OrderStatus.remediating],  # 不通过退回
    OrderStatus.closed: [OrderStatus.archived],
    OrderStatus.archived: [],
}


class RemediationService:
    """整改工单服务——创建、状态转换、查询。"""

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._init_db()

    def _get_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        os.makedirs(os.path.dirname(self._db_path) if os.path.dirname(self._db_path) else ".", exist_ok=True)
        conn = self._get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS remediation_orders (
                order_id TEXT PRIMARY KEY,
                red_flag_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'discovered',
                assigned_to TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                resolved_at TEXT,
                score INTEGER,
                notes TEXT DEFAULT '[]',
                history TEXT DEFAULT '[]'
            )
        """)
        conn.commit()
        conn.close()

    def create_from_red_flag(
        self,
        red_flag_id: str,
        assigned_to: str = "",
    ) -> dict:
        """从红灯事件创建整改工单。"""
        order_id = uuid4().hex[:12]
        now = datetime.now(timezone.utc).isoformat()
        history = [{"status": "discovered", "timestamp": now, "operator": "system"}]

        conn = self._get_db()
        conn.execute(
            "INSERT INTO remediation_orders (order_id, red_flag_id, status, assigned_to, created_at, notes, history) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (order_id, red_flag_id, "discovered", assigned_to, now, "[]", json.dumps(history)),
        )
        conn.commit()
        conn.close()

        logger.info("整改工单创建: id=%s red_flag=%s assigned_to=%s", order_id, red_flag_id, assigned_to)
        return self.get_order(order_id)

    def transition(self, order_id: str, target_status: str, operator: str = "system") -> dict:
        """状态转换。校验合法性后更新。"""
        order = self.get_order(order_id)
        if not order:
            return {"error": f"order not found: {order_id}"}

        current = OrderStatus(order["status"])
        target = OrderStatus(target_status)

        if target not in _VALID_TRANSITIONS.get(current, []):
            return {
                "error": f"非法状态转换: {current.value} → {target.value}",
                "valid_targets": [s.value for s in _VALID_TRANSITIONS.get(current, [])],
            }

        now = datetime.now(timezone.utc).isoformat()
        history: list = json.loads(order.get("history", "[]"))
        history.append({"status": target.value, "timestamp": now, "operator": operator})

        conn = self._get_db()
        conn.execute(
            "UPDATE remediation_orders SET status=?, history=? WHERE order_id=?",
            (target.value, json.dumps(history), order_id),
        )
        if target == OrderStatus.archived:
            conn.execute(
                "UPDATE remediation_orders SET resolved_at=? WHERE order_id=?",
                (now, order_id),
            )
        conn.commit()
        conn.close()

        return self.get_order(order_id)

    def get_order(self, order_id: str) -> dict | None:
        """获取单个工单。"""
        conn = self._get_db()
        row = conn.execute("SELECT * FROM remediation_orders WHERE order_id=?", (order_id,)).fetchone()
        conn.close()
        if not row:
            return None
        return dict(row)

    def list_orders(self, status_filter: str | None = None) -> list[dict]:
        """列出工单，可选按状态过滤。"""
        conn = self._get_db()
        if status_filter:
            rows = conn.execute(
                "SELECT * FROM remediation_orders WHERE status=? ORDER BY created_at DESC",
                (status_filter,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM remediation_orders ORDER BY created_at DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]
