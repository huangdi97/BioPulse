"""SOAP 决策验证与转换方法，包含意见管理功能。"""

import json

from fastapi import HTTPException
from starlette import status as http_status

from cloud.app.repositories import AsyncMdtOpinionsRepository, SoapDecisionsRepository


def _row(row, json_keys=None):
    """将数据库行转为字典并解析指定的 JSON 字段。

    Args:
        row: 数据库行
        json_keys: 需解析为 JSON 的字段名列表

    Returns:
        转换后的字典，None 输入返回 None
    """
    if row is None:
        return None
    d = dict(row)
    for k in json_keys or []:
        if k in d and isinstance(d[k], str):
            d[k] = json.loads(d[k])
    return d


class SoapDecisionValidatorMixin:
    """SOAP 决策校验与转换方法，提供异步意见管理。"""

    def add_opinion(
        self,
        decision_id: int,
        opinion: str,
        stance: str,
        supporting_data: str,
        confidence: float,
        attachments: list,
        user_id,
        role: str,
    ) -> dict:
        """为决策添加异步 MDT 意见。

        Args:
            decision_id: 决策 ID
            opinion: 意见内容
            stance: 立场（support/oppose/neutral）
            supporting_data: 支撑数据
            confidence: 置信度
            attachments: 附件列表
            user_id: 提交者 ID
            role: 提交者角色

        Returns:
            创建的意见记录
        """
        decisions_repo = SoapDecisionsRepository(self._connection())
        opinions_repo = AsyncMdtOpinionsRepository(self._connection())
        dec = decisions_repo.get_by_id(decision_id)
        if not dec or not dec.get("is_active"):
            raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Decision not found")
        opinion_id = opinions_repo.create(
            {
                "decision_id": decision_id,
                "contributor_id": user_id,
                "contributor_role": role,
                "opinion": opinion,
                "supporting_data": supporting_data,
                "stance": stance,
                "confidence": confidence,
                "attachments": json.dumps(attachments, ensure_ascii=False),
                "updated_at": "NOW()",
            }
        )
        opinions_repo.execute("UPDATE async_mdt_opinions SET updated_at=NOW() WHERE id=?", (opinion_id,))
        self.db.commit()
        row = opinions_repo.get_by_id(opinion_id)
        return _row(row, ["attachments"])

    def list_opinions(self, decision_id: int) -> list:
        """列出决策的所有异步意见。

        Args:
            decision_id: 决策 ID

        Returns:
            意见列表
        """
        decisions_repo = SoapDecisionsRepository(self._connection())
        opinions_repo = AsyncMdtOpinionsRepository(self._connection())
        dec = decisions_repo.get_by_id(decision_id)
        if not dec or not dec.get("is_active"):
            raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Decision not found")
        rows = opinions_repo.list_by_decision(decision_id)
        return [_row(r, ["attachments"]) for r in rows]
