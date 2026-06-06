"""异常检测服务：规则管理、告警查询与监控统计。"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sales_assistant.app.repositories import AlertRepository, AnomalyRuleRepository
from sales_assistant.app.services.base import BaseService


class AnomalyService(BaseService):
    """异常检测服务：自定义规则配置、自动检测异常并生成告警。"""

    def create_rule(self, body, user_id: int) -> int:
        """创建异常检测规则。

        Args:
            body: 规则请求体，含指标、运算符、阈值等。
            user_id: 创建者用户ID。

        Returns:
            新创建的规则ID。
        """
        now = datetime.now(timezone.utc).isoformat()
        repo = AnomalyRuleRepository(self.db)
        return repo.create(
            body.model_dump(),
            extra={"created_by": user_id, "created_at": now, "updated_at": now},
        )

    def list_rules(
        self,
        page: int,
        page_size: int,
        metric: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> tuple:
        """分页查询异常检测规则列表。

        Args:
            page: 页码。
            page_size: 每页条数。
            metric: 按指标筛选。
            severity: 按严重程度筛选。

        Returns:
            (记录列表, 总条数) 元组。
        """
        repo = AnomalyRuleRepository(self.db)
        conditions: List[str] = ["is_active = 1"]
        params: list = []
        if metric:
            conditions.append("metric = ?")
            params.append(metric)
        if severity:
            conditions.append("severity = ?")
            params.append(severity)
        return repo.paginate(page, page_size, conditions, params)

    def update_rule(self, rule_id: int, body) -> dict:
        """更新异常检测规则。

        Args:
            rule_id: 规则ID。
            body: 更新数据。

        Returns:
            更新后的规则详情。
        """
        repo = AnomalyRuleRepository(self.db)
        row = repo.get_or_404(rule_id)
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(rule_id, updates)
        return dict(repo.get_by_id(rule_id))

    def delete_rule(self, rule_id: int) -> None:
        """软删除异常检测规则。

        Args:
            rule_id: 规则ID。
        """
        repo = AnomalyRuleRepository(self.db)
        repo.get_or_404(rule_id)
        repo.soft_delete(rule_id)

    def _compute_metric(self, metric: str) -> float:
        if metric == "visit_frequency":
            cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            row = self.db.execute(
                """SELECT COUNT(*) FROM visit_hcp v
                   JOIN schedule s ON v.schedule_id = s.id
                   WHERE s.created_at > ?""",
                (cutoff,),
            ).fetchone()
            return float(row[0])
        elif metric == "strategy_effectiveness":
            row = self.db.execute(
                "SELECT COALESCE(AVG(CAST(effectiveness AS REAL)), 0) FROM strategy_simulation WHERE effectiveness IS NOT NULL"
            ).fetchone()
            return float(row[0])
        elif metric == "total_visits":
            row = self.db.execute("SELECT COUNT(*) FROM schedule").fetchone()
            return float(row[0])
        elif metric == "follow_up_rate":
            total = self.db.execute("SELECT COUNT(*) FROM visit_hcp").fetchone()[0]
            if total == 0:
                return 0.0
            fu = self.db.execute("SELECT COUNT(*) FROM visit_hcp WHERE follow_up_required = 1").fetchone()[0]
            return fu / total
        return 0.0

    def _compare(self, value: float, operator: str, threshold: float) -> bool:
        if operator == ">":
            return value > threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<":
            return value < threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return abs(value - threshold) < 0.001
        return False

    def check_anomalies(self) -> int:
        """执行异常检测，扫描所有活跃规则并生成告警。

        Returns:
            新生成的告警数量。
        """
        rule_repo = AnomalyRuleRepository(self.db)
        alert_repo = AlertRepository(self.db)
        rules = rule_repo.list_all(conditions=["is_active = 1"])
        now = datetime.now(timezone.utc).isoformat()
        created = 0
        for rule in rules:
            value = self._compute_metric(rule["metric"])
            if self._compare(value, rule["operator"], rule["threshold"]):
                alert_repo.create(
                    {
                        "rule_id": rule["id"],
                        "entity_type": "system",
                        "entity_id": 0,
                        "detected_value": value,
                        "severity": rule["severity"],
                        "message": f"{rule['rule_name']}: {value} {rule['operator']} {rule['threshold']}",
                        "status": "open",
                        "detected_at": now,
                        "created_at": now,
                    }
                )
                created += 1
        return created

    def list_alerts(
        self,
        page: int,
        page_size: int,
        severity: Optional[str] = None,
        status_val: Optional[str] = None,
    ) -> tuple:
        """分页查询告警列表。

        Args:
            page: 页码。
            page_size: 每页条数。
            severity: 按严重程度筛选。
            status_val: 按状态筛选。

        Returns:
            (记录列表, 总条数) 元组。
        """
        repo = AlertRepository(self.db)
        conditions: List[str] = []
        params: list = []
        if severity:
            conditions.append("severity = ?")
            params.append(severity)
        if status_val:
            conditions.append("status = ?")
            params.append(status_val)
        return repo.paginate(page, page_size, conditions, params, order_by="detected_at DESC")

    def update_alert(self, alert_id: int, body, user_id: int) -> dict:
        """更新告警状态。

        Args:
            alert_id: 告警ID。
            body: 更新数据，含状态和处理人。
            user_id: 操作用户ID。

        Returns:
            更新后的告警详情。
        """
        repo = AlertRepository(self.db)
        repo.get_or_404(alert_id)
        now = datetime.now(timezone.utc).isoformat()
        updates = {"status": body.status}
        if body.status in ("resolved", "acknowledged"):
            updates["resolved_at"] = now
            updates["resolved_by"] = body.resolved_by or user_id
        repo.update(alert_id, updates)
        return dict(repo.get_by_id(alert_id))

    def anomaly_stats(self) -> dict:
        """获取异常统计概览。

        Returns:
            按严重程度、规则分布和7天趋势的分组统计数据。
        """
        by_severity = self.db.execute("SELECT severity, COUNT(*) AS cnt FROM anomaly_alert GROUP BY severity").fetchall()
        by_rule = self.db.execute("SELECT rule_id, COUNT(*) AS cnt FROM anomaly_alert GROUP BY rule_id").fetchall()
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        trend = self.db.execute(
            "SELECT DATE(detected_at) AS day, COUNT(*) AS cnt FROM anomaly_alert WHERE detected_at >= ? GROUP BY DATE(detected_at) ORDER BY day",
            (cutoff,),
        ).fetchall()
        return {
            "by_severity": {r["severity"]: r["cnt"] for r in by_severity},
            "by_rule": {str(r["rule_id"]): r["cnt"] for r in by_rule},
            "trend_7d": [{"date": r["day"], "count": r["cnt"]} for r in trend],
        }
