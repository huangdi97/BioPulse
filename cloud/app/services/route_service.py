"""路由服务，负责路由规则的增删改查与基于 DeepSeek AI 的执行调度。"""

from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    RouteLogsRepository,
    RouteRulesRepository,
    RouteStatsRepository,
)
from cloud.app.services.base import BaseService
from cloud.app.services.route_calculation import RouteCalculationMixin
from shared.base import validate_columns
from shared.columns import TABLE_ROUTE_RULES_COLS

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
TIMEOUT_SECONDS = 30


class RouteService(RouteCalculationMixin, BaseService):
    """路由服务，提供路由规则的增删改查、基于 DeepSeek AI 的执行调度与日志统计。"""

    def create_rule(
        self,
        name: str,
        priority: int,
        condition_field: str,
        condition_operator: str,
        condition_value: str,
        target_role_id: int,
        fallback_role_id: Optional[int],
        max_tokens: int,
        temperature: float,
        created_by: int,
    ) -> dict:
        """创建一条新的路由规则。

        Args:
            name: 规则名称
            priority: 优先级，数值越小越优先
            condition_field: 条件字段名
            condition_operator: 条件运算符 (contains, equals, starts_with)
            condition_value: 条件匹配值
            target_role_id: 匹配后指派的目标 Agent 角色 ID
            fallback_role_id: 可选，回退角色 ID
            max_tokens: DeepSeek API 最大 token 数
            temperature: DeepSeek API 温度参数
            created_by: 创建者用户 ID

        Returns:
            新创建的路由规则记录字典
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rules_repo = RouteRulesRepository(self.db)
        rule_id = rules_repo.create(
            {
                "name": name,
                "priority": priority,
                "condition_field": condition_field,
                "condition_operator": condition_operator,
                "condition_value": condition_value,
                "target_role_id": target_role_id,
                "fallback_role_id": fallback_role_id,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "created_by": created_by,
                "created_at": now,
                "updated_at": now,
            }
        )
        return rules_repo.get_by_id(rule_id)

    def list_rules(self) -> list:
        """获取所有路由规则列表。

        Returns:
            路由规则记录列表，按优先级排序
        """
        rules_repo = RouteRulesRepository(self.db)
        return rules_repo.list_all_ordered()

    def update_rule(
        self,
        rule_id: int,
        name: Optional[str] = None,
        priority: Optional[int] = None,
        condition_value: Optional[str] = None,
        target_role_id: Optional[int] = None,
        is_active: Optional[int] = None,
    ) -> dict:
        """更新一条路由规则的指定字段。

        Args:
            rule_id: 规则 ID
            name: 可选，新规则名称
            priority: 可选，新优先级
            condition_value: 可选，新条件值
            target_role_id: 可选，新目标角色 ID
            is_active: 可选，启用状态 (1=启用, 0=禁用)

        Returns:
            更新后的路由规则记录字典

        Raises:
            HTTPException: 规则不存在时返回 404
        """
        rules_repo = RouteRulesRepository(self.db)
        existing = rules_repo.get_by_id(rule_id)
        if not existing:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Rule not found")
        updates = {}
        for f in ["name", "priority", "condition_value", "target_role_id", "is_active"]:
            v = locals().get(f)
            if v is not None:
                updates[f] = v
        if updates:
            updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            validate_columns(updates, "route_rules", TABLE_ROUTE_RULES_COLS)
            rules_repo.update(rule_id, updates)
        return rules_repo.get_by_id(rule_id)

    def delete_rule(self, rule_id: int) -> None:
        """删除一条路由规则。

        Args:
            rule_id: 规则 ID

        Raises:
            HTTPException: 规则不存在时返回 404
        """
        rules_repo = RouteRulesRepository(self.db)
        existing = rules_repo.get_by_id(rule_id)
        if not existing:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Rule not found")
        rules_repo.delete(rule_id)

    def list_logs(
        self,
        role_id: Optional[int] = None,
        source: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """分页查询路由执行日志。

        Args:
            role_id: 可选，按指派角色 ID 过滤
            source: 可选，按来源过滤
            date_from: 可选，开始日期
            date_to: 可选，结束日期
            page: 页码，默认 1
            page_size: 每页条数，默认 20

        Returns:
            包含 items、total、page、page_size、total_pages 的字典
        """
        logs_repo = RouteLogsRepository(self.db)
        total, total_pages, items = logs_repo.list_filtered(
            role_id=role_id,
            source=source,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_log(self, log_id: int) -> dict:
        """获取单条路由执行日志详情。

        Args:
            log_id: 日志 ID

        Returns:
            日志记录字典

        Raises:
            HTTPException: 日志不存在时返回 404
        """
        logs_repo = RouteLogsRepository(self.db)
        row = logs_repo.get_by_id(log_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Log not found")
        return row

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
