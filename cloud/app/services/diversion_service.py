"""窜货检测服务 — 检测产品流向与授权区域的一致性，接入全息稽核引擎。"""

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any

from cloud.app.compliance.triangulation import HolographicAuditEngine

_NOTIFIER = None


def _get_notifier():
    global _NOTIFIER
    if _NOTIFIER is None:
        from cloud.app.agent_runtime.notifier import Notifier

        _NOTIFIER = Notifier()
    return _NOTIFIER


class DiversionDetectionService:
    """窜货检测服务 — 检测产品流向与授权区域的一致性，记录窜货日志。"""

    def __init__(self, db: sqlite3.Connection, notifier=None):
        self.db = db
        self.notifier = notifier
        self._ensure_tables()

    def _ensure_tables(self):
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS diversion_log ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "product TEXT, region TEXT, authorized_region TEXT, "
            "quantity INTEGER, dealer_id TEXT, rep_id TEXT, "
            "is_diversion INTEGER, severity TEXT, "
            "reason TEXT, created_at TEXT, "
            "holographic_score REAL, "
            "holographic_level TEXT, "
            "holographic_findings TEXT"
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

        holographic_score = None
        holographic_level = None
        holographic_findings = None

        if is_diversion:
            try:
                tri_result = self.run_holographic_audit_check(distribution_data)
                holographic_score = tri_result.get("holographic_score")
                holographic_level = tri_result.get("holographic_level")
                findings = tri_result.get("findings", [])
                if findings:
                    holographic_findings = json.dumps(findings, ensure_ascii=False)
                    max_finding_score = max(f.get("score", 0) for f in findings)
                    if max_finding_score >= 0.9 and severity:
                        severity = "high"
                        reason += f"；全息稽核确认高风险（评分 {max_finding_score}）"
                    elif max_finding_score >= 0.5 and severity and severity != "high":
                        severity = "medium"
                        reason += f"；全息稽核提示异常（评分 {max_finding_score}）"
                if holographic_level == "high" and severity:
                    severity = "high"
            except Exception:
                pass

        if is_diversion and severity == "high":
            self._send_red_light_notification(product, region, authorized_region, quantity, rep_id, reason)

        self.db.execute(
            "INSERT INTO diversion_log (product, region, authorized_region, "
            "quantity, dealer_id, rep_id, is_diversion, severity, reason, created_at, "
            "holographic_score, holographic_level, holographic_findings) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
                holographic_score,
                holographic_level,
                holographic_findings,
            ),
        )
        self.db.commit()

        return {
            "is_diversion": is_diversion,
            "reason": reason,
            "severity": severity,
            "holographic_score": holographic_score,
            "holographic_level": holographic_level,
        }

    def _send_red_light_notification(self, product: str, region: str, authorized_region: str, quantity: int, rep_id: str, reason: str):
        notifier = self.notifier or _get_notifier()
        message = (
            f"[红灯] 窜货检测异常 — 产品：{product}，"
            f"实际区域：{region}，授权区域：{authorized_region}，"
            f"数量：{quantity}，代表：{rep_id}，原因：{reason}"
        )
        notifier.send(message, priority="high", channels=["in_app"])
        try:
            notifier.send(message, priority="high", channels=["webhook"])
        except Exception:
            pass

    def run_holographic_audit_check(self, distribution_data: dict[str, Any]) -> dict[str, Any]:
        """将窜货数据送入全息稽核引擎进行深度交叉验证。

        调用 HolographicAuditEngine.check() 对 distribution_data 做多维度分析，
        返回引擎的置信度评分与异常发现。
        """
        engine = HolographicAuditEngine(db=self.db)
        result = engine.check(
            expense_data=None,
            visit_data=None,
            distribution_data=[distribution_data],
            distribution_area=[
                {"product": distribution_data.get("product", ""), "authorized_region": distribution_data.get("authorized_region", "")}
            ],
        )
        return {
            "holographic_score": result.confidence_score,
            "holographic_level": result.suspicion_level,
            "findings": [asdict(f) for f in result.findings],
        }

    def get_diversion_records(self, rep_id: str, days: int = 30) -> list[dict]:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        rows = self.db.execute(
            "SELECT * FROM diversion_log WHERE rep_id = ? AND created_at >= ? ORDER BY created_at DESC",
            (rep_id, cutoff),
        ).fetchall()
        cols = [d[0] for d in self.db.execute("SELECT * FROM diversion_log LIMIT 0").description]
        return [dict(zip(cols, row)) for row in rows]
