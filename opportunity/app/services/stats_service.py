"""统计服务，提供平台数据的统计分析功能。"""

from typing import Optional

from opportunity.app.repositories import StatsRepository
from shared.base_service import BaseService

"""统计报表服务，按阶段和产品维度汇总商机统计数据。"""


class StatsService(BaseService):
    """统计报表：总量、总金额、按阶段分布、按产品分布、均价、赢单率。"""

    def get_stats(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """汇总商机统计报表。

        Args:
            start_date: 可选的统计开始日期。
            end_date: 可选的统计结束日期。

        Returns:
            包含总量、总金额、阶段分布、产品分布、均价和赢单率的字典。

        Raises:
            sqlite3.Error: 当统计查询失败时由仓储层抛出。
        """
        repo = StatsRepository(self._connection())
        total_count, total_value = repo.get_totals(start_date, end_date)

        by_stage: dict = {}
        won_count = 0
        lost_count = 0
        for r in repo.get_by_stage(start_date, end_date):
            stage = r[0] or "unknown"
            count = r[1]
            val = r[2]
            by_stage[stage] = {"count": count, "value": val}
            if stage == "won":
                won_count = count
            elif stage == "lost":
                lost_count = count

        by_product: list = []
        for r in repo.get_by_product(start_date, end_date):
            by_product.append({"product": r[0], "count": r[1], "value": r[2]})

        avg_value = round(total_value / total_count, 2) if total_count > 0 else 0.0

        total_closed = won_count + lost_count
        win_rate = round(won_count / total_closed * 100, 1) if total_closed > 0 else 0.0

        return {
            "total_count": total_count,
            "total_value": total_value,
            "by_stage": by_stage,
            "by_product": by_product,
            "avg_value": avg_value,
            "win_rate": win_rate,
        }
