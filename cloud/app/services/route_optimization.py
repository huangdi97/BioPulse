"""路由优化方法，包含路由统计与仪表盘功能。"""

from cloud.app.repositories import RouteLogsRepository, RouteStatsRepository


class RouteOptimizationMixin:
    """路由优化方法，提供路由统计与仪表盘数据。"""

    def get_stats(self) -> list:
        """获取路由统计数据。

        Returns:
            包含角色名称的统计记录列表
        """
        stats_repo = RouteStatsRepository(self.db)
        return stats_repo.list_with_role_name()

    def get_dashboard(self) -> dict:
        """获取路由仪表盘汇总数据。

        Returns:
            包含总执行次数、角色分布、平均延迟和最近日志的字典
        """
        logs_repo = RouteLogsRepository(self.db)
        total = logs_repo.count()
        if total == 0:
            return {
                "total_executions": 0,
                "role_distribution": [],
                "avg_latency_ms": 0,
                "recent_logs": [],
            }
        rows = logs_repo.role_distribution()
        role_dist = [
            {
                "role_id": r["assigned_role_id"],
                "role_name": r["assigned_role_name"],
                "count": r["cnt"],
                "percentage": round(r["cnt"] / total * 100, 2),
            }
            for r in rows
        ]
        avg_lat = logs_repo.avg_latency()
        recent = logs_repo.list_recent(10)
        return {
            "total_executions": total,
            "role_distribution": role_dist,
            "avg_latency_ms": round(avg_lat, 2),
            "recent_logs": recent,
        }
