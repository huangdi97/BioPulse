"""信任审计服务负责系统信任度评估与审计。"""

import hashlib
import json
from datetime import datetime, timedelta

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    AuditChainBlocksRepository,
    FederatedNodesRepository,
)
from shared.base_service import BaseService
from shared.datetime_utils import now as _now


def _since_datetime(days: int) -> str:
    return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")


def _block_to_dict(r) -> dict:
    return {
        k: r[k]
        for k in (
            "id",
            "block_hash",
            "prev_block_hash",
            "block_data",
            "block_type",
            "created_by",
            "node_id",
            "timestamp",
        )
    }


class TrustAuditService(BaseService):
    """TrustAudit 服务类。"""

    def calculate_trust_score(self, node_id: str) -> dict:
        """calculate_trust_score 操作。

        Args:
            node_id: 描述

        Returns:
            描述
        """
        repo = FederatedNodesRepository(self._connection())
        row = repo.get_by_node_id(node_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

        reliability = row["reliability_score"] or 0.0
        total_samples = row["total_samples"] or 0
        round_count = row["round_count"] or 0
        last_heartbeat = row["last_heartbeat"] or ""

        samples_factor = min(total_samples / 10000, 1.0)
        rounds_factor = min(round_count / 100, 1.0)

        if last_heartbeat:
            try:
                hb_dt = datetime.strptime(last_heartbeat[:19], "%Y-%m-%d %H:%M:%S")
                hours_since = (datetime.utcnow() - hb_dt).total_seconds() / 3600
                if hours_since <= 1:
                    recency_factor = 1.0
                elif hours_since <= 24:
                    recency_factor = 0.8
                elif hours_since <= 168:
                    recency_factor = 0.5
                else:
                    recency_factor = 0.2
            except ValueError:
                recency_factor = 0.5
        else:
            recency_factor = 0.0

        trust_score = reliability * 0.40 + samples_factor * 0.25 + rounds_factor * 0.20 + recency_factor * 0.15
        trust_score = round(min(max(trust_score, 0.0), 1.0), 4)

        return {
            "node_id": node_id,
            "trust_score": trust_score,
            "reliability_score": reliability,
            "samples_factor": round(samples_factor, 4),
            "rounds_factor": round(rounds_factor, 4),
            "recency_factor": round(recency_factor, 4),
            "total_samples": total_samples,
            "round_count": round_count,
            "last_heartbeat": last_heartbeat,
        }

    def create_audit_block(self, data: dict, block_type: str = "audit", node_id: str = "", created_by: str = "") -> dict:
        """create_audit_block 操作。

        Args:
            data: 描述
            block_type: 描述
            node_id: 描述
            created_by: 描述

        Returns:
            描述
        """
        block_repo = AuditChainBlocksRepository(self._connection())
        node_repo = FederatedNodesRepository(self._connection())

        if node_id:
            node_row = node_repo.get_by_node_id(node_id)
            if not node_row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

        latest = block_repo.get_latest()
        prev_block_hash = latest["block_hash"] if latest else ""

        block_data_str = json.dumps(data, ensure_ascii=False, sort_keys=True)
        raw = prev_block_hash + block_data_str
        block_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        row_id = block_repo.create(
            {
                "block_hash": block_hash,
                "prev_block_hash": prev_block_hash,
                "block_data": block_data_str,
                "block_type": block_type,
                "created_by": created_by,
                "node_id": node_id,
                "timestamp": _now(),
            }
        )
        row = block_repo.get_by_id(row_id)
        return _block_to_dict(row)

    def verify_chain(self) -> dict:
        """verify_chain 操作。

        Returns:
            描述
        """
        block_repo = AuditChainBlocksRepository(self._connection())
        blocks = block_repo.list_all(order_by="id ASC")

        valid = True
        broken_at = None
        total = len(blocks)

        for i, block in enumerate(blocks):
            expected_prev = blocks[i - 1]["block_hash"] if i > 0 else ""
            if block["prev_block_hash"] != expected_prev:
                valid = False
                broken_at = block["id"]
                break

            block_data_str = block["block_data"]
            if isinstance(block_data_str, str):
                try:
                    data_obj = json.loads(block_data_str)
                except json.JSONDecodeError:
                    data_obj = {}
            else:
                data_obj = block_data_str

            recomputed_raw = expected_prev + json.dumps(data_obj, ensure_ascii=False, sort_keys=True)
            recomputed_hash = hashlib.sha256(recomputed_raw.encode("utf-8")).hexdigest()
            if recomputed_hash != block["block_hash"]:
                valid = False
                broken_at = block["id"]
                break

        return {
            "valid": valid,
            "total_blocks": total,
            "broken_at": broken_at,
        }

    def get_chain(self, node_id: str = "", limit: int = 50) -> list:
        """get_chain 操作。

        Args:
            node_id: 描述
            limit: 描述

        Returns:
            描述
        """
        block_repo = AuditChainBlocksRepository(self._connection())
        rows = block_repo.get_chain(node_id=node_id, limit=limit)
        return [_block_to_dict(r) for r in rows]
