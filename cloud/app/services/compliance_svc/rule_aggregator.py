"""规则结果聚合模块，提供记录查询与分页。"""

import json
import math

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import ComplianceAuditRecordsRepository
from shared.base import PaginatedResponse, success


def _parse_json(raw: str, default=None):
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else raw


def _n404(name="Resource"):
    raise HTTPException(status.HTTP_404_NOT_FOUND, f"{name} not found")


class RuleAggregatorMixin:
    """规则聚合混入类，提供审计记录查询与分页。"""

    def list_records(
        self,
        message_type,
        risk_level,
        passed,
        date_from,
        date_to,
        page,
        page_size,
    ) -> dict:
        repo = ComplianceAuditRecordsRepository(self._connection())
        conditions, params = [], []
        if message_type:
            conditions.append("message_type=?")
            params.append(message_type)
        if risk_level:
            conditions.append("risk_level=?")
            params.append(risk_level)
        if passed is not None:
            conditions.append("passed=?")
            params.append(passed)
        if date_from:
            conditions.append("created_at >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("created_at <= ?")
            params.append(date_to)
        total, _, rows = repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )
        total_pages = math.ceil(total / max(page_size, 1))
        return success(
            data=PaginatedResponse(
                items=rows,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )
        )

    def get_record(self, record_id: int) -> dict:
        repo = ComplianceAuditRecordsRepository(self._connection())
        row = repo.get_by_id(record_id)
        if not row:
            _n404("Record")
        data = row
        data["violations"] = _parse_json(data["violations"], [])
        data["ai_analysis"] = _parse_json(data["ai_analysis"], {})
        return success(data=data)
