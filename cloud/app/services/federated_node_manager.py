"""联邦节点管理服务，负责联邦学习节点的注册、启停与状态管理。"""

from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import FederatedNodesRepository
from cloud.app.services.base import BaseService


def _node_to_dict(row) -> dict:
    return {
        k: row[k]
        for k in (
            "id",
            "node_id",
            "node_name",
            "node_type",
            "organization",
            "status",
            "endpoint_url",
            "public_key",
            "data_summary",
            "last_heartbeat",
            "round_count",
            "total_samples",
            "reliability_score",
            "is_active",
            "registered_at",
            "updated_at",
        )
    }


class NodeManager(BaseService):
    """FederatedNode 节点管理类。"""

    def register_node(
        self,
        node_id: str,
        node_name: str = "",
        node_type: str = "partner",
        organization: str = "",
        endpoint_url: str = "",
        public_key: str = "",
        data_summary: str = "{}",
    ) -> dict:
        """register_node 操作。

        Args:
            node_id: 描述
            node_name: 描述
            node_type: 描述
            organization: 描述
            endpoint_url: 描述
            public_key: 描述
            data_summary: 描述

        Returns:
            描述
        """
        repo = FederatedNodesRepository(self.db)
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        existing = repo.get_by_node_id(node_id)
        if existing:
            repo.update(
                existing["id"],
                {
                    "node_name": node_name,
                    "node_type": node_type,
                    "organization": organization,
                    "endpoint_url": endpoint_url,
                    "public_key": public_key,
                    "data_summary": data_summary,
                    "updated_at": now,
                },
            )
            row = repo.get_by_id(existing["id"])
        else:
            row_id = repo.create(
                {
                    "node_id": node_id,
                    "node_name": node_name,
                    "node_type": node_type,
                    "organization": organization,
                    "status": "pending",
                    "endpoint_url": endpoint_url,
                    "public_key": public_key,
                    "data_summary": data_summary,
                    "registered_at": now,
                    "updated_at": now,
                }
            )
            row = repo.get_by_id(row_id)
        return _node_to_dict(row)

    def list_nodes(
        self,
        status_filter: Optional[str] = None,
        node_type: Optional[str] = None,
    ) -> list:
        """list_nodes 操作。

        Args:
            status_filter: 描述
            node_type: 描述

        Returns:
            描述
        """
        repo = FederatedNodesRepository(self.db)
        conditions, params = [], []
        if status_filter:
            conditions.append("status=?")
            params.append(status_filter)
        if node_type:
            conditions.append("node_type=?")
            params.append(node_type)
        rows = repo.list_all(
            conditions=conditions or None,
            params=params or None,
            order_by="registered_at DESC",
        )
        return [_node_to_dict(r) for r in rows]

    def get_node(self, node_id: str) -> dict:
        """get_node 操作。

        Args:
            node_id: 描述

        Returns:
            描述
        """
        repo = FederatedNodesRepository(self.db)
        row = repo.get_by_node_id(node_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
        return _node_to_dict(row)

    def heartbeat(self, node_id: str, data_summary: Optional[str] = None) -> dict:
        """heartbeat 操作。

        Args:
            node_id: 描述
            data_summary: 描述

        Returns:
            描述
        """
        repo = FederatedNodesRepository(self.db)
        row = repo.get_by_node_id(node_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        update = {"last_heartbeat": now, "status": "online", "updated_at": now}
        if data_summary is not None:
            update["data_summary"] = data_summary
        repo.update(row["id"], update)
        updated = repo.get_by_id(row["id"])
        return _node_to_dict(updated)

    def update_status(
        self,
        node_id: str,
        status_val: str,
        reliability_score: Optional[float] = None,
    ) -> dict:
        """update_status 操作。

        Args:
            node_id: 描述
            status_val: 描述
            reliability_score: 描述

        Returns:
            描述
        """
        repo = FederatedNodesRepository(self.db)
        row = repo.get_by_node_id(node_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        update = {"status": status_val, "updated_at": now}
        if reliability_score is not None:
            update["reliability_score"] = reliability_score
        repo.update(row["id"], update)
        updated = repo.get_by_id(row["id"])
        return _node_to_dict(updated)
