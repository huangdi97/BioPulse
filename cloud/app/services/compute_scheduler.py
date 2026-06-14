"""隐私计算调度模块，管理联邦学习轮次与贡献审计。"""

# FROZEN — 代码保留不迭代。参见 BioPulse-整体战略规划-v2.3-final.md 第2章

import json
from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    FedAuditContributionsRepository,
    FederatedRoundsRepository,
)


def _round_to_dict(row) -> dict:
    """将联邦学习轮次行转换为字典。"""
    return {
        "id": row["id"],
        "round_id": row["round_id"],
        "model_name": row["model_name"],
        "round_number": row["round_number"],
        "participant_count": row["participant_count"],
        "aggregation_method": row["aggregation_method"],
        "global_metrics": row["global_metrics"],
        "status": row["status"],
        "created_at": row["created_at"],
        "completed_at": row["completed_at"],
    }


class ComputeSchedulerMixin:
    """计算调度混入类，提供联邦学习与贡献审计功能。"""

    def init_federated(self, model_name: str, num_rounds: int, aggregation_method: str) -> list:
        """初始化多轮联邦学习任务。"""
        repo = FederatedRoundsRepository(self._connection())
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        for rn in range(1, num_rounds + 1):
            round_id = f"fl:{uuid4()}"
            repo.create(
                {
                    "round_id": round_id,
                    "model_name": model_name,
                    "round_number": rn,
                    "aggregation_method": aggregation_method,
                    "status": "pending",
                    "created_at": now,
                }
            )
        rows = repo.list_all(
            conditions=["model_name=?", "created_at=?"],
            params=[model_name, now],
            order_by="round_number ASC",
        )
        return [_round_to_dict(r) for r in rows]

    def submit_federated(self, round_id: str, participant_id: str, metrics: dict, update_summary: str) -> dict:
        """提交联邦学习参与方更新。"""
        repo = FederatedRoundsRepository(self._connection())
        rows = repo.list_all(conditions=["round_id=?"], params=[round_id])
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Federated round not found",
            )
        row = rows[0]
        participant_count = (row["participant_count"] or 0) + 1
        existing_metrics = json.loads(row["global_metrics"] or "{}")
        if metrics:
            for k, v in metrics.items():
                existing_metrics[k] = v
        repo.update(
            row["id"],
            {
                "participant_count": participant_count,
                "global_metrics": json.dumps(existing_metrics, ensure_ascii=False),
            },
        )
        updated = repo.list_all(conditions=["round_id=?"], params=[round_id])
        return _round_to_dict(updated[0])

    def list_federated_rounds(self, model_name=None, status_filter=None) -> list:
        """查询联邦学习轮次列表。"""
        repo = FederatedRoundsRepository(self._connection())
        conditions, params = [], []
        if model_name:
            conditions.append("model_name=?")
            params.append(model_name)
        if status_filter:
            conditions.append("status=?")
            params.append(status_filter)
        rows = repo.list_all(
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )
        return [_round_to_dict(r) for r in rows]

    def prove_contribution(self, contribution_id: int, prover_sub: str) -> dict:
        """证明贡献记录的真实性。"""
        repo = FedAuditContributionsRepository(self._connection())
        row = repo.get_by_id(contribution_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contribution not found",
            )
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        return {
            "contribution_id": row["id"],
            "contributor_did": row["contributor_did"],
            "contribution_type": row["contribution_type"],
            "payload_summary": row["payload_summary"],
            "weight": row["weight"],
            "verified": row["verified"],
            "audit_chain_hash": row["audit_chain_hash"],
            "proven_at": now,
            "prover": prover_sub,
        }

    def verify_contribution(self, contribution_id: int) -> dict:
        """验证贡献记录是否存在及可信。"""
        repo = FedAuditContributionsRepository(self._connection())
        row = repo.get_by_id(contribution_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contribution not found",
            )
        return {
            "exists": True,
            "contribution_id": row["id"],
            "contributor_did": row["contributor_did"],
            "contribution_type": row["contribution_type"],
            "weight": row["weight"],
            "verified": bool(row["verified"]),
            "audit_chain_hash": row["audit_chain_hash"],
            "created_at": row["created_at"],
        }
