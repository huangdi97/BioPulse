"""联邦节点服务，提供联邦节点的注册、管理与聚合分析入口。"""

from typing import Optional

from shared.base_service import BaseService

from .federated_node_aggregator import FedAggregator
from .federated_node_manager import NodeManager


class FederatedNodeService(BaseService):
    """FederatedNode 服务类。"""

    def __init__(self, db):
        super().__init__(db)
        self._node_mgr = NodeManager(db)
        self._aggregator = FedAggregator(db)

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
        return self._node_mgr.register_node(
            node_id=node_id,
            node_name=node_name,
            node_type=node_type,
            organization=organization,
            endpoint_url=endpoint_url,
            public_key=public_key,
            data_summary=data_summary,
        )

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
        return self._node_mgr.list_nodes(
            status_filter=status_filter,
            node_type=node_type,
        )

    def get_node(self, node_id: str) -> dict:
        """get_node 操作。

        Args:
            node_id: 描述

        Returns:
            描述
        """
        return self._node_mgr.get_node(node_id=node_id)

    def heartbeat(self, node_id: str, data_summary: Optional[str] = None) -> dict:
        """heartbeat 操作。

        Args:
            node_id: 描述
            data_summary: 描述

        Returns:
            描述
        """
        return self._node_mgr.heartbeat(
            node_id=node_id,
            data_summary=data_summary,
        )

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
        return self._node_mgr.update_status(
            node_id=node_id,
            status_val=status_val,
            reliability_score=reliability_score,
        )

    def get_dashboard(self, days: Optional[int] = None) -> dict:
        """get_dashboard 操作。

        Args:
            days: 描述

        Returns:
            描述
        """
        return self._aggregator.get_dashboard(days=days)

    def export_dashboard_csv(self, days: Optional[int] = None) -> str:
        """export_dashboard_csv 操作。

        Args:
            days: 描述

        Returns:
            描述
        """
        return self._aggregator.export_dashboard_csv(days=days)

    def get_audit_log(self, days: Optional[int] = None) -> dict:
        """get_audit_log 操作。

        Args:
            days: 描述

        Returns:
            描述
        """
        return self._aggregator.get_audit_log(days=days)

    def get_compliance_summary(self) -> list:
        """get_compliance_summary 操作。

        Returns:
            描述
        """
        return self._aggregator.get_compliance_summary()

    def export_audit_log_csv(self, days: Optional[int] = None) -> str:
        """export_audit_log_csv 操作。

        Args:
            days: 描述

        Returns:
            描述
        """
        return self._aggregator.export_audit_log_csv(days=days)
