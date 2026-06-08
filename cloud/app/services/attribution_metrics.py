"""商机归因指标计算方法。"""

from datetime import datetime, timedelta, timezone


def _today_str() -> str:
    """返回 UTC 今天的日期字符串 YYYY-MM-DD。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _days_ago(n: int) -> str:
    """返回 n 天前的 UTC 日期字符串。

    Args:
        n: 回溯天数

    Returns:
        YYYY-MM-DD 格式的日期字符串
    """
    return (datetime.now(timezone.utc) - timedelta(days=n)).strftime("%Y-%m-%d")


_FACTOR_META = [
    {
        "name": "visit_frequency",
        "display_name": "拜访频率",
        "max_score": 35,
        "description": "近30天客户拜访次数。>5次给30-35分，3-5次给20-29分，1-2次给5-19分，0次给0分",
    },
    {
        "name": "product_match",
        "display_name": "产品匹配度",
        "max_score": 25,
        "description": "商机阶段匹配度。negotiation/won给20-25分，proposal给10-19分，lead/qualify给0-9分",
    },
    {
        "name": "hcp_relation",
        "display_name": "HCP关系强度",
        "max_score": 20,
        "description": "近60天与该客户关联的正面交互占比*20",
    },
    {
        "name": "competitor_threat",
        "display_name": "竞品活动",
        "max_score": 15,
        "description": "竞品活动记录扣分，最多-15分",
    },
    {
        "name": "time_window",
        "display_name": "时间窗口",
        "max_score": 10,
        "description": "距close_date<30天给8-10分，30-60天给4-7分，>60天或空给0分",
    },
    {
        "name": "stage_weight",
        "display_name": "阶段权重",
        "max_score": 10,
        "description": "won=10, negotiation=8, proposal=6, qualify=3, lead=1, lost=0",
    },
]

_STAGE_WEIGHTS = {
    "won": 10,
    "closed_won": 10,
    "negotiation": 8,
    "proposal": 6,
    "qualify": 3,
    "qualification": 3,
    "lead": 1,
    "lost": 0,
    "closed_lost": 0,
}

_RECOMMENDATIONS = {
    "visit_frequency": "建议增加HCP拜访频次，提升商机推进速度。",
    "product_match": "产品匹配度处于高位，建议加快商务谈判进程。",
    "hcp_relation": "HCP关系是当前最强驱动因子，建议维持并深化合作关系。",
    "competitor_threat": "竞品活动活跃，建议加强差异化价值传递并密切关注竞品动向。",
    "time_window": "时间窗口紧迫，建议优先处理该商机的关键决策节点。",
    "stage_weight": "商机阶段权重较高，建议保持当前推进节奏。",
}


def _calc_month_days(close_date: str) -> int:
    """计算距关闭日期的剩余天数。

    Args:
        close_date: ISO 格式的关闭日期字符串

    Returns:
        剩余天数，解析失败返回 -1
    """
    try:
        clean = close_date.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (dt - datetime.now(timezone.utc)).days
    except (ValueError, TypeError):
        return -1


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
