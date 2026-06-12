"""A2A 能力发现方法，包含 Agent 搜索与事件查询。"""

import logging

from shared.datetime_utils import row_to_dict

logger = logging.getLogger(__name__)


class A2aDiscoveryMixin:
    """A2A 能力发现方法，提供 Agent 搜索与事件查询。"""

    def list_agents(self, agent_type=None, status=None, capability=None):
        """按条件搜索 Agent 列表。

        Args:
            agent_type: 按类型筛选
            status: 按状态筛选
            capability: 按能力关键词筛选

        Returns:
            Agent 列表（在线优先）
        """
        sql = "SELECT * FROM agent_registry WHERE 1=1"
        params = []
        if agent_type:
            sql += " AND agent_type=?"
            params.append(agent_type)
        if status:
            sql += " AND status=?"
            params.append(status)
        if capability:
            sql += " AND capabilities LIKE ?"
            params.append(f'%"{capability}"%')
        sql += " ORDER BY CASE WHEN status='online' THEN 0 ELSE 1 END, created_at DESC"
        rows = self.db.execute(sql, params).fetchall()
        return [row_to_dict(r, "capabilities", "metadata", "input_data", "output_data", "detail") for r in rows]

    def list_events(self, event_type=None, agent_key=None, limit=50):
        """查询 Agent 网络事件。

        Args:
            event_type: 按事件类型筛选
            agent_key: 按 Agent 键筛选
            limit: 最大返回数

        Returns:
            事件列表
        """
        sql = "SELECT * FROM agent_network_events WHERE 1=1"
        params = []
        if event_type:
            sql += " AND event_type=?"
            params.append(event_type)
        if agent_key:
            sql += " AND agent_key=?"
            params.append(agent_key)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = self.db.execute(sql, params).fetchall()
        return [row_to_dict(r, "capabilities", "metadata", "input_data", "output_data", "detail") for r in rows]
