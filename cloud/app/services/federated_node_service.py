import csv
import io
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import FederatedNodesRepository, FederatedRoundsRepository
from cloud.app.repositories.audit_repository import AuditLogsRepository, FedAuditContributionsRepository
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


def _since_datetime(days: int) -> str:
    return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")


def _audit_log_to_dict(r) -> dict:
    return {
        k: r[k]
        for k in (
            "id",
            "user_id",
            "action",
            "entity_type",
            "entity_id",
            "detail",
            "source_end",
            "ip_address",
            "created_at",
        )
    }


def _contribution_to_dict(r) -> dict:
    return {
        k: r[k]
        for k in (
            "id",
            "contributor_did",
            "contribution_type",
            "payload_hash",
            "payload_summary",
            "weight",
            "verified",
            "verified_by",
            "audit_chain_hash",
            "created_at",
        )
    }


def _to_csv(rows: list[dict], fieldnames: list[str]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


class FederatedNodeService(BaseService):
    """FederatedNode 服务类。"""

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

    def get_dashboard(self, days: Optional[int] = None) -> dict:
        """get_dashboard 操作。

        Args:
            days: 描述

        Returns:
            描述
        """
        node_repo = FederatedNodesRepository(self.db)
        round_repo = FederatedRoundsRepository(self.db)
        audit_repo = AuditLogsRepository(self.db)
        contrib_repo = FedAuditContributionsRepository(self.db)

        all_nodes = node_repo.get_all()
        total = len(all_nodes)
        online = sum(1 for n in all_nodes if n["status"] == "online")
        total_samples = sum(n["total_samples"] or 0 for n in all_nodes)
        total_rounds = sum(n["round_count"] or 0 for n in all_nodes)
        status_dist = {}
        type_dist = {}
        for n in all_nodes:
            s = n["status"]
            status_dist[s] = status_dist.get(s, 0) + 1
            t = n["node_type"]
            type_dist[t] = type_dist.get(t, 0) + 1

        since = _since_datetime(days) if days else None
        if since:
            audit_cond = ["created_at>=?"]
            audit_params = [since]
        else:
            audit_cond = None
            audit_params = None
        recent_audit_logs = audit_repo.list_all(conditions=audit_cond, params=audit_params, order_by="created_at DESC")
        recent_audit_logs = [_audit_log_to_dict(r) for r in recent_audit_logs[:20]]

        contribs = contrib_repo.get_recent(limit=10)
        contribs = [_contribution_to_dict(c) for c in contribs]

        compliance_count = sum(1 for n in all_nodes if n["status"] == "online" and (n["reliability_score"] or 0) >= 0.8)
        data_usage_count = sum(1 for c in contribs if c.get("verified") is True)

        recent_rounds = round_repo.list_all(order_by="created_at DESC", params=[])
        recent_rounds = [dict(r) for r in recent_rounds[:5]]
        return {
            "total_nodes": total,
            "online_nodes": online,
            "total_rounds": total_rounds,
            "total_samples": total_samples,
            "status_distribution": status_dist,
            "type_distribution": type_dist,
            "recent_rounds": recent_rounds,
            "audit_logs": recent_audit_logs,
            "audit_contributions": contribs,
            "compliant_nodes": compliance_count,
            "verified_data_usage": data_usage_count,
        }

    def export_dashboard_csv(self, days: Optional[int] = None) -> str:
        """export_dashboard_csv 操作。

        Args:
            days: 描述

        Returns:
            描述
        """
        data = self.get_dashboard(days=days)
        rows = []
        for log in data["audit_logs"]:
            rows.append(
                {
                    "id": log["id"],
                    "action": log["action"],
                    "entity_type": log["entity_type"],
                    "entity_id": log["entity_id"],
                    "detail": log.get("detail", ""),
                    "created_at": log["created_at"],
                }
            )
        if not rows:
            rows = [{"id": "", "action": "", "entity_type": "", "entity_id": "", "detail": "", "created_at": ""}]
        return _to_csv(rows, ["id", "action", "entity_type", "entity_id", "detail", "created_at"])

    def get_audit_log(self, days: Optional[int] = None) -> dict:
        """get_audit_log 操作。

        Args:
            days: 描述

        Returns:
            描述
        """
        audit_repo = AuditLogsRepository(self.db)
        contrib_repo = FedAuditContributionsRepository(self.db)
        since = _since_datetime(days) if days else None
        if since:
            audit_cond = ["created_at>=?"]
            audit_params = [since]
        else:
            audit_cond = None
            audit_params = None
        logs = audit_repo.list_all(conditions=audit_cond, params=audit_params, order_by="created_at DESC")
        logs = [_audit_log_to_dict(r) for r in logs]
        contribs = contrib_repo.list_all(order_by="created_at DESC")
        contribs = [_contribution_to_dict(c) for c in contribs]
        return {"operation_logs": logs, "compliance_checks": contribs}

    def get_compliance_summary(self) -> list:
        """get_compliance_summary 操作。

        Returns:
            描述
        """
        repo = FederatedNodesRepository(self.db)
        all_nodes = repo.get_all()
        result = []
        for n in all_nodes:
            result.append(
                {
                    "node_id": n["node_id"],
                    "node_name": n["node_name"],
                    "status": n["status"],
                    "reliability_score": n["reliability_score"],
                    "is_active": n["is_active"],
                    "total_samples": n["total_samples"],
                    "last_heartbeat": n["last_heartbeat"],
                    "compliant": n["status"] == "online" and (n["reliability_score"] or 0) >= 0.8,
                }
            )
        return result

    def export_audit_log_csv(self, days: Optional[int] = None) -> str:
        """export_audit_log_csv 操作。

        Args:
            days: 描述

        Returns:
            描述
        """
        data = self.get_audit_log(days=days)
        rows = []
        for log in data["operation_logs"]:
            rows.append(
                {
                    "type": "operation",
                    "id": log["id"],
                    "user_id": log.get("user_id", ""),
                    "action": log["action"],
                    "entity_type": log["entity_type"],
                    "entity_id": log["entity_id"],
                    "detail": log.get("detail", ""),
                    "created_at": log["created_at"],
                }
            )
        for c in data["compliance_checks"]:
            rows.append(
                {
                    "type": "compliance",
                    "id": c["id"],
                    "user_id": c.get("contributor_did", ""),
                    "action": c.get("contribution_type", ""),
                    "entity_type": "fed_contribution",
                    "entity_id": c.get("payload_hash", ""),
                    "detail": c.get("payload_summary", ""),
                    "created_at": c["created_at"],
                }
            )
        if not rows:
            rows = [
                {
                    "type": "",
                    "id": "",
                    "user_id": "",
                    "action": "",
                    "entity_type": "",
                    "entity_id": "",
                    "detail": "",
                    "created_at": "",
                }
            ]
        return _to_csv(rows, ["type", "id", "user_id", "action", "entity_type", "entity_id", "detail", "created_at"])
