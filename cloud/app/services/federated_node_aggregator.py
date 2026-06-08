"""联邦节点聚合服务，提供联邦学习节点的数据汇总与分析。"""

import csv
import io
from datetime import datetime, timedelta
from typing import Optional

from cloud.app.repositories import FederatedNodesRepository, FederatedRoundsRepository
from cloud.app.repositories.audit_repository import AuditLogsRepository, FedAuditContributionsRepository
from cloud.app.services.base import BaseService


def _since_datetime(days: int) -> str:
    """计算当前时间减去指定天数后的日期时间字符串。

    Args:
        days: 减去的天数。

    Returns:
        YYYY-MM-DD HH:MM:SS 格式的字符串。
    """
    return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")


def _audit_log_to_dict(r) -> dict:
    """将审计日志行对象转换为字典，仅保留指定字段。

    Args:
        r: 数据库行对象。

    Returns:
        包含 id, user_id, action, entity_type, entity_id, detail, source_end, ip_address, created_at 的字典。
    """
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
    """将联邦审计贡献行对象转换为字典，仅保留指定字段。

    Args:
        r: 数据库行对象。

    Returns:
        包含 id, contributor_did, contribution_type, payload_hash, payload_summary, weight, verified, verified_by, audit_chain_hash, created_at 的字典。
    """
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
    """将字典列表导出为 CSV 格式字符串。

    Args:
        rows: 行数据列表。
        fieldnames: CSV 列名列表。

    Returns:
        CSV 格式字符串。
    """
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


class FedAggregator(BaseService):
    """联邦节点聚合服务，提供仪表盘、审计日志、合规摘要与 CSV 导出。"""

    def get_dashboard(self, days: Optional[int] = None) -> dict:
        """获取联邦学习仪表盘汇总。

        Args:
            days: 统计周期天数，None 为全部

        Returns:
            含节点统计、审计日志和贡献记录的字典
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
        """导出仪表盘数据为 CSV。

        Args:
            days: 统计周期天数

        Returns:
            CSV 格式字符串
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
        """获取审计日志与合规贡献记录。

        Args:
            days: 统计周期天数

        Returns:
            含 operation_logs 和 compliance_checks 的字典
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
        """获取所有节点的合规摘要。

        Returns:
            节点合规状态列表（含 compliant 标志）
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
        """导出审计日志为 CSV。

        Args:
            days: 统计周期天数

        Returns:
            CSV 格式字符串
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
