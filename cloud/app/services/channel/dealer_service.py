"""渠道经销商服务 — CRUD、返利、窜货热力图。"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Any

from shared.base_service import BaseService


class DealerService(BaseService):
    """经销商管理服务，管理经销商信息、计算返利、聚合窜货热力图。"""

    def __init__(self, db: sqlite3.Connection | None = None):
        super().__init__(db)
        self._ensure_tables()

    def _ensure_tables(self):
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS dealers ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name TEXT NOT NULL, "
            "authorized_regions TEXT DEFAULT '[]', "
            "sales_target REAL DEFAULT 0, "
            "created_at TEXT"
            ")"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS dealer_sales ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "dealer_id INTEGER NOT NULL, "
            "amount REAL NOT NULL, "
            "period TEXT, "
            "created_at TEXT"
            ")"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS dealer_payments ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "dealer_id INTEGER NOT NULL, "
            "total_receivable REAL NOT NULL, "
            "total_received REAL NOT NULL, "
            "period TEXT, "
            "created_at TEXT"
            ")"
        )
        self.db.commit()

    # ── CRUD ──

    def create(self, name: str, authorized_regions: list[str] | None = None, sales_target: float = 0) -> dict:
        regions_json = json.dumps(authorized_regions or [], ensure_ascii=False)
        cursor = self.db.execute(
            "INSERT INTO dealers (name, authorized_regions, sales_target, created_at) VALUES (?, ?, ?, ?)",
            (name, regions_json, sales_target, datetime.now().isoformat()),
        )
        self.db.commit()
        return {"id": cursor.lastrowid, "name": name, "authorized_regions": authorized_regions or [], "sales_target": sales_target}

    def _row_to_dealer(self, row) -> dict:
        cols = [d[0] for d in self.db.execute("SELECT * FROM dealers LIMIT 0").description]
        dealer = dict(zip(cols, row))
        dealer["authorized_regions"] = json.loads(dealer.get("authorized_regions") or "[]")
        return dealer

    def list_dealers(self) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT * FROM dealers ORDER BY id").fetchall()
        return [self._row_to_dealer(r) for r in rows]

    def get_dealer(self, dealer_id: int) -> dict[str, Any] | None:
        row = self.db.execute("SELECT * FROM dealers WHERE id = ?", (dealer_id,)).fetchone()
        return self._row_to_dealer(row) if row else None

    # ── 返利 ──

    def calculate_rebate(self, dealer_id: int) -> dict[str, Any]:
        dealer = self.get_dealer(dealer_id)
        if not dealer:
            return {"error": "dealer not found", "dealer_id": dealer_id}

        # 销量得分 (40%) — 实际销售额 / 销售目标 * 100，上限 100
        sales_row = self.db.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM dealer_sales WHERE dealer_id = ?",
            (dealer_id,),
        ).fetchone()
        total_sales = sales_row["total"]
        target = dealer["sales_target"]
        sales_score = min(100, total_sales / target * 100) if target > 0 else 0

        # 合规得分 (30%) — 近 30 天每次窜货扣 20 分
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()
        diversion_row = self.db.execute(
            "SELECT COUNT(*) AS cnt FROM diversion_log WHERE dealer_id = ? AND is_diversion = 1 AND created_at >= ?",
            (str(dealer_id), cutoff),
        ).fetchone()
        diversion_cnt = diversion_row["cnt"]
        compliance_score = max(0, 100 - diversion_cnt * 20)

        # 回款得分 (30%) — 已回款 / 应收 * 100，上限 100
        payment_row = self.db.execute(
            "SELECT COALESCE(SUM(total_receivable), 0) AS receivable, "
            "COALESCE(SUM(total_received), 0) AS received "
            "FROM dealer_payments WHERE dealer_id = ?",
            (dealer_id,),
        ).fetchone()
        receivable, received = payment_row["receivable"], payment_row["received"]
        payment_score = min(100, received / receivable * 100) if receivable > 0 else 0

        total = sales_score * 0.4 + compliance_score * 0.3 + payment_score * 0.3

        return {
            "dealer_id": dealer_id,
            "dealer_name": dealer["name"],
            "sales_score": round(sales_score, 2),
            "compliance_score": round(compliance_score, 2),
            "payment_score": round(payment_score, 2),
            "total_rebate": round(total, 2),
        }

    # ── 热力图 ──

    def get_diversion_heatmap(self) -> list[dict[str, Any]]:
        rows = self.db.execute(
            "SELECT region, COUNT(*) AS count, "
            "COALESCE(AVG(CAST(holographic_score AS REAL)), 0) AS avg_score "
            "FROM diversion_log WHERE is_diversion = 1 "
            "GROUP BY region ORDER BY count DESC"
        ).fetchall()
        result = []
        for row in rows:
            result.append(
                {
                    "region": row["region"],
                    "count": row["count"],
                    "avg_holographic_score": round(row["avg_score"], 2),
                }
            )
        return result
