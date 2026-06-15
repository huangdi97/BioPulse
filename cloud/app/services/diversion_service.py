"""窜货检测服务 — 检测产品流向与授权区域的一致性。"""

import sqlite3
from datetime import datetime, timedelta


class DiversionDetectionService:
    """窜货检测服务 — 检测产品流向与授权区域的一致性，记录窜货日志。"""

    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self._ensure_tables()

    def _ensure_tables(self):
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS diversion_log ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "product TEXT, region TEXT, authorized_region TEXT, "
            "quantity INTEGER, dealer_id TEXT, rep_id TEXT, "
            "is_diversion INTEGER, severity TEXT, "
            "reason TEXT, created_at TEXT"
            ")"
        )
        self.db.execute("CREATE TABLE IF NOT EXISTS product_authorized_regions (product TEXT PRIMARY KEY, authorized_region TEXT NOT NULL)")
        self.db.commit()

    def _get_authorized_region(self, product: str) -> str | None:
        row = self.db.execute(
            "SELECT authorized_region FROM product_authorized_regions WHERE product = ?",
            (product,),
        ).fetchone()
        if row:
            return row[0] if isinstance(row, tuple) else row["authorized_region"]
        return None

    def check_distribution(self, distribution_data: dict) -> dict:
        product = distribution_data.get("product", "")
        region = distribution_data.get("region", "")
        quantity = distribution_data.get("quantity", 0) or 0
        dealer_id = distribution_data.get("dealer_id", "")
        rep_id = distribution_data.get("rep_id", "")

        authorized_region = distribution_data.get("authorized_region") or self._get_authorized_region(product)

        is_diversion = False
        reason = ""
        severity = "low"

        if authorized_region and region != authorized_region and quantity > 10:
            is_diversion = True
            reason = f"产品 {product} 流向区域 {region} 与授权区域 {authorized_region} 不一致，数量 {quantity} > 10"
            if quantity > 100:
                severity = "high"
            elif quantity > 50:
                severity = "medium"

        if not authorized_region:
            reason = f"产品 {product} 无授权区域配置，跳过窜货检测"

        self.db.execute(
            "INSERT INTO diversion_log (product, region, authorized_region, "
            "quantity, dealer_id, rep_id, is_diversion, severity, reason, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                product,
                region,
                authorized_region or "",
                quantity,
                dealer_id,
                rep_id,
                int(is_diversion),
                severity,
                reason,
                datetime.now().isoformat(),
            ),
        )
        self.db.commit()

        return {
            "is_diversion": is_diversion,
            "reason": reason,
            "severity": severity,
        }

    def get_diversion_records(self, rep_id: str, days: int = 30) -> list[dict]:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        rows = self.db.execute(
            "SELECT * FROM diversion_log WHERE rep_id = ? AND created_at >= ? ORDER BY created_at DESC",
            (rep_id, cutoff),
        ).fetchall()
        return [dict(row) for row in rows]
