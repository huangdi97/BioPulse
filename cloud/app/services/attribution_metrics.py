"""商机归因指标计算方法。"""

from cloud.app.services.attribution_assigner import _calc_month_days, _days_ago


class AttributionMetricsMixin:
    """归因因子指标打分方法。"""

    def _count_visits(self, customer_id: int) -> int:
        """统计近30天客户拜访次数并转换为拜访频率得分。

        Args:
            customer_id: 客户 ID

        Returns:
            拜访频率得分（0-35）
        """
        since = _days_ago(30)
        row = self.db.execute(
            "SELECT COUNT(*) AS cnt FROM customer_interactions WHERE customer_id=? AND conducted_at>=?",
            (customer_id, since),
        ).fetchone()
        count = row["cnt"] if row else 0
        if count > 5:
            return min(30 + (count - 5), 35)
        if count >= 3:
            return 20 + (count - 3) * 5
        if count >= 1:
            return 5 + (count - 1) * 14
        return 0

    def _calc_product_match(self, stage: str) -> int:
        """根据商机阶段计算产品匹配度得分。

        Args:
            stage: 商机阶段

        Returns:
            匹配度得分（0-25）
        """
        stage_lower = stage.lower()
        if stage_lower in ("negotiation", "closed_won", "won"):
            return 25
        if stage_lower in ("proposal",):
            return 15
        if stage_lower in ("qualify", "qualification"):
            return 5
        return 0

    def _calc_hcp_relation(self, customer_id: int) -> int:
        """计算近60天与该客户关联的 HCP 关系强度得分。

        Args:
            customer_id: 客户 ID

        Returns:
            关系强度得分（0-20）
        """
        since = _days_ago(60)
        rows = self.db.execute(
            "SELECT outcome FROM episodic_memory WHERE related_entity_id=? AND created_at>=?",
            (customer_id, since),
        ).fetchall()
        if not rows:
            return 0
        positive = sum(1 for r in rows if r["outcome"] in ("success", "positive", "completed"))
        ratio = positive / len(rows)
        return int(ratio * 20)

    def _calc_competitor_threat(self, customer_id: int) -> int:
        """计算近60天竞品活动威胁得分。

        Args:
            customer_id: 客户 ID

        Returns:
            竞品威胁得分（0-15）
        """
        since = _days_ago(60)
        row = self.db.execute(
            "SELECT COUNT(*) AS cnt FROM market_intel_items WHERE item_type='competitor' AND collected_at>=?",
            (since,),
        ).fetchone()
        count = row["cnt"] if row else 0
        return min(count * 5, 15)

    def _calc_time_window(self, close_date: str) -> int:
        """根据关闭日期计算时间窗口紧迫度得分。

        Args:
            close_date: 关闭日期字符串

        Returns:
            时间窗口得分（0-10）
        """
        if not close_date:
            return 0
        days = _calc_month_days(close_date)
        if days < 0:
            return 0
        if days < 30:
            return 10
        if days <= 60:
            return 7
        return 0
