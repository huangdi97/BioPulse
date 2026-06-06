# FROZEN — 代码保留不迭代。参见一云四端-整体战略规划-v2.3-final.md 第2章
"""隐私计算服务，管理安全计算任务、联邦学习轮次与贡献审计。"""

import json
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    FedAuditContributionsRepository,
    FederatedRoundsRepository,
    PrivacyComputeJobsRepository,
)
from cloud.app.services.base import BaseService

SCHEME_MAP = {
    "low": "DP",
    "medium": "DP+FL",
    "high": "FL+HE",
    "critical": "DP+FL+HE",
}


def _job_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "job_id": row["job_id"],
        "compute_type": row["compute_type"],
        "sensitivity_level": row["sensitivity_level"],
        "data_summary": row["data_summary"],
        "selected_scheme": row["selected_scheme"],
        "status": row["status"],
        "epsilon_used": row["epsilon_used"],
        "noise_level": row["noise_level"],
        "result_summary": row["result_summary"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
        "completed_at": row["completed_at"],
    }


def _round_to_dict(row) -> dict:
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


class ComputeService(BaseService):
    """隐私计算服务，提供可信计算任务、联邦学习及贡献验证功能。"""

    def create_job(self, compute_type: str, sensitivity_level: str, data_summary: str, user_id: int) -> dict:
        repo = PrivacyComputeJobsRepository(self.db)
        job_id = f"pc:{uuid4()}"
        scheme = SCHEME_MAP.get(sensitivity_level, "DP+FL")
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        row_id = repo.create(
            {
                "job_id": job_id,
                "compute_type": compute_type,
                "sensitivity_level": sensitivity_level,
                "data_summary": data_summary,
                "selected_scheme": scheme,
                "status": "pending",
                "created_by": user_id,
                "created_at": now,
            }
        )
        row = repo.get_by_id(row_id)
        return _job_to_dict(row)

    def list_jobs(self, status_filter: Optional[str] = None, compute_type: Optional[str] = None) -> list:
        repo = PrivacyComputeJobsRepository(self.db)
        conditions, params = [], []
        if status_filter:
            conditions.append("status=?")
            params.append(status_filter)
        if compute_type:
            conditions.append("compute_type=?")
            params.append(compute_type)
        rows = repo.list_all(
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )
        return [_job_to_dict(r) for r in rows]

    def get_job(self, job_id: str) -> dict:
        repo = PrivacyComputeJobsRepository(self.db)
        rows = repo.list_all(conditions=["job_id=?"], params=[job_id])
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Compute job not found",
            )
        return _job_to_dict(rows[0])

    def init_federated(self, model_name: str, num_rounds: int, aggregation_method: str) -> list:
        repo = FederatedRoundsRepository(self.db)
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
        repo = FederatedRoundsRepository(self.db)
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

    def list_federated_rounds(self, model_name: Optional[str] = None, status_filter: Optional[str] = None) -> list:
        repo = FederatedRoundsRepository(self.db)
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
        repo = FedAuditContributionsRepository(self.db)
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
        repo = FedAuditContributionsRepository(self.db)
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
