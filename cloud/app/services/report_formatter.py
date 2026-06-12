"""报告格式输出方法，包含纠偏训练列表查询与更新。"""

import math
from typing import Optional

from cloud.app.repositories import TrainingCorrectionsRepository
from cloud.app.services.report_templates import _n404
from shared.base import PaginatedResponse, success


class ReportFormatterMixin:
    """报告格式输出方法，提供纠偏训练相关功能。"""

    def list_corrections(
        self,
        category: Optional[str],
        severity: Optional[str],
        status: Optional[str],
        page: int,
        page_size: int,
    ) -> dict:
        """分页查询纠偏训练列表。

        Args:
            category: 按类别筛选
            severity: 按严重程度筛选
            status: 按状态筛选
            page: 页码
            page_size: 每页条数

        Returns:
            分页结果
        """
        repo = TrainingCorrectionsRepository(self._connection())
        conditions, params = [], []
        if category:
            conditions.append("category=?")
            params.append(category)
        if severity:
            conditions.append("severity=?")
            params.append(severity)
        if status:
            conditions.append("status=?")
            params.append(status)
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

    def update_correction(self, correction_id: int, body) -> dict:
        """更新纠偏训练状态。

        Args:
            correction_id: 纠偏记录 ID
            body: 请求体（含 status、assigned_to）

        Returns:
            更新后的纠偏记录
        """
        repo = TrainingCorrectionsRepository(self._connection())
        row = repo.get_by_id(correction_id)
        if not row:
            _n404("Correction")
        updates = {}
        if body.status is not None:
            updates["status"] = body.status
        if body.assigned_to is not None:
            updates["assigned_to"] = body.assigned_to
        if updates:
            repo.update(correction_id, updates)
        return success(data=repo.get_by_id(correction_id))
