"""销售机会服务，负责机会的增删改查、阶段流转与销售漏斗分析。"""

from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import CustomersRepository, OpportunitiesRepository
from cloud.app.services.opportunity_scoring import (
    STAGE_ORDER,
    VALID_STAGES,
    calc_stage_probability,
    get_opp_or_404,
    row_to_dict,
    validate_stage_transition,
)
from shared.base import validate_columns
from shared.base_service import BaseService
from shared.columns import TABLE_OPPORTUNITIES_COLS


class OpportunityAnalysisMixin:
    """销售漏斗分析、阶段概率和阶段流转方法。"""

    def _stage_probability(self, stage: str) -> int:
        return calc_stage_probability(stage)

    def _validate_stage_transition(self, current: str, target: str) -> None:
        validate_stage_transition(current, target)

    def get_pipeline(self) -> dict:
        """获取销售漏斗数据，按阶段统计机会数量和金额。

        Returns:
            包含 pipeline 列表的字典，每项含 stage、count、total_value
        """
        opp_repo = OpportunitiesRepository(self._connection())
        rows = self.db.execute(
            f"""SELECT stage, COUNT(*) as count, SUM(estimated_value) as total_value
            FROM {opp_repo.table_name} WHERE is_active = 1 AND stage != 'lost'
            GROUP BY stage"""
        ).fetchall()

        stage_map = {r["stage"]: {"count": r["count"], "total_value": r["total_value"]} for r in rows}
        pipeline = []
        for s in STAGE_ORDER:
            if s == "lost":
                continue
            data = stage_map.get(s, {"count": 0, "total_value": 0.0})
            pipeline.append({"stage": s, "count": data["count"], "total_value": data["total_value"]})

        return {"pipeline": pipeline}

    def transition_stage(self, opp_id: int, stage: str, actual_value: Optional[float] = None) -> dict:
        """执行机会阶段流转操作。

        Args:
            opp_id: 机会 ID
            stage: 目标阶段，必须是有效阶段之一
            actual_value: 可选，当流转到 won 阶段时的实际成交金额

        Returns:
            更新后的机会记录字典

        Raises:
            HTTPException: 机会不存在、阶段无效或从终态流转时抛出
        """
        row = self._get_opp_or_404(opp_id)

        if stage not in VALID_STAGES:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid stage. Must be one of: {VALID_STAGES}",
            )

        self._validate_stage_transition(row["stage"], stage)

        opp_repo = OpportunitiesRepository(self._connection())
        probability = self._stage_probability(stage)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        updates_fields = {"stage": stage, "probability": probability, "updated_at": now}

        if stage == "won":
            if actual_value is not None:
                updates_fields["actual_value"] = actual_value
            elif row["actual_value"] is not None:
                updates_fields["actual_value"] = row["actual_value"]
            else:
                updates_fields["actual_value"] = row["estimated_value"]

        validate_columns(updates_fields, "opportunities", TABLE_OPPORTUNITIES_COLS)
        opp_repo.update(opp_id, updates_fields)

        row = self._get_opp_or_404(opp_id)
        return self._row_to_dict(row)


class OpportunityService(OpportunityAnalysisMixin, BaseService):
    """销售机会业务服务，组合机会分析能力与基础 CRUD。"""

    def create_opportunity(
        self,
        customer_id: int,
        name: str,
        description: str,
        stage: str,
        estimated_value: float,
        actual_value: float,
        assigned_to: Optional[int],
        close_date: Optional[str],
        notes: str,
        user_id: int,
    ) -> dict:
        """创建销售机会并按阶段设置默认赢率。

        Args:
            customer_id: 关联客户ID，客户必须处于active状态。
            name: 机会名称。
            description: 机会描述。
            stage: 机会阶段，必须属于有效阶段集合。
            estimated_value: 预估金额。
            actual_value: 实际成交金额。
            assigned_to: 可选的负责人用户ID。
            close_date: 可选的预计或实际关闭日期。
            notes: 机会备注。
            user_id: 创建人用户ID。

        Returns:
            新建机会的字典表示。

        Raises:
            HTTPException: 当客户不存在、客户非活跃或阶段非法时抛出。
        """
        cust_repo = CustomersRepository(self._connection())
        placeholders = ", ".join(cust_repo.cols)
        customer = self.db.execute(
            f"SELECT {placeholders} FROM {cust_repo.table_name} WHERE id=? AND status='active'",
            (customer_id,),
        ).fetchone()
        if not customer:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Customer not found or inactive")
        if stage not in VALID_STAGES:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid stage. Must be one of: {VALID_STAGES}",
            )
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        probability = self._stage_probability(stage)
        opp_repo = OpportunitiesRepository(self._connection())
        row_id = opp_repo.create(
            {
                "customer_id": customer_id,
                "name": name,
                "description": description,
                "stage": stage,
                "probability": probability,
                "estimated_value": estimated_value,
                "actual_value": actual_value,
                "assigned_to": assigned_to,
                "close_date": close_date,
                "notes": notes,
                "created_by": user_id,
                "created_at": now,
                "updated_at": now,
            }
        )
        row = opp_repo.get_by_id(row_id)
        return row_to_dict(self.db, row)

    def list_opportunities(
        self,
        stage: Optional[str] = None,
        assigned_to: Optional[int] = None,
        customer_id: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """按条件分页查询活跃销售机会。

        Args:
            stage: 可选的机会阶段过滤条件。
            assigned_to: 可选的负责人用户ID过滤条件。
            customer_id: 可选的客户ID过滤条件。
            search: 可选的名称或描述模糊搜索关键词。
            page: 当前页码。
            page_size: 每页数量。

        Returns:
            包含机会列表和分页字段的字典。

        Raises:
            HTTPException: 当底层数据库查询失败时由调用栈抛出。
        """
        opp_repo = OpportunitiesRepository(self._connection())
        conditions = ["is_active = 1"]
        params: list = []
        if stage:
            conditions.append("stage = ?")
            params.append(stage)
        if assigned_to is not None:
            conditions.append("assigned_to = ?")
            params.append(assigned_to)
        if customer_id is not None:
            conditions.append("customer_id = ?")
            params.append(customer_id)
        if search:
            conditions.append("(name LIKE ? OR description LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        total, _, items = opp_repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params,
            order_by="updated_at DESC",
        )
        return {
            "items": [row_to_dict(self.db, r) for r in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_opportunity(self, opp_id: int) -> dict:
        """读取单个销售机会。

        Args:
            opp_id: 销售机会ID。

        Returns:
            销售机会的字典表示。

        Raises:
            HTTPException: 当机会不存在时抛出404。
        """
        row = get_opp_or_404(self.db, opp_id)
        return row_to_dict(self.db, row)

    def update_opportunity(
        self,
        opp_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        stage: Optional[str] = None,
        estimated_value: Optional[float] = None,
        actual_value: Optional[float] = None,
        assigned_to: Optional[int] = None,
        close_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """更新销售机会字段并校验阶段流转。

        Args:
            opp_id: 销售机会ID。
            name: 可选的新机会名称。
            description: 可选的新机会描述。
            stage: 可选的新阶段。
            estimated_value: 可选的新预估金额。
            actual_value: 可选的新实际金额。
            assigned_to: 可选的新负责人用户ID。
            close_date: 可选的新关闭日期。
            notes: 可选的新备注。

        Returns:
            更新后的销售机会字典。

        Raises:
            HTTPException: 当机会不存在、阶段非法或阶段流转不允许时抛出。
        """
        get_opp_or_404(self.db, opp_id)
        opp_repo = OpportunitiesRepository(self._connection())
        updates = {}
        field_map = {
            "name": name,
            "description": description,
            "estimated_value": estimated_value,
            "actual_value": actual_value,
            "assigned_to": assigned_to,
            "close_date": close_date,
            "notes": notes,
        }
        for k, v in field_map.items():
            if v is not None:
                updates[k] = v
        if stage is not None:
            placeholders = ", ".join(opp_repo.cols)
            current_row = self.db.execute(
                f"SELECT {placeholders} FROM {opp_repo.table_name} WHERE id=?",
                (opp_id,),
            ).fetchone()
            if current_row:
                self._validate_stage_transition(current_row["stage"], stage)
            if stage not in VALID_STAGES:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid stage. Must be one of: {VALID_STAGES}",
                )
            updates["stage"] = stage
            updates["probability"] = self._stage_probability(stage)
        if updates:
            updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            validate_columns(updates, "opportunities", TABLE_OPPORTUNITIES_COLS)
            opp_repo.update(opp_id, updates)
        row = get_opp_or_404(self.db, opp_id)
        return row_to_dict(self.db, row)

    def delete_opportunity(self, opp_id: int) -> None:
        """软删除销售机会。

        Args:
            opp_id: 销售机会ID。

        Returns:
            None。

        Raises:
            HTTPException: 当机会不存在时抛出404。
        """
        get_opp_or_404(self.db, opp_id)
        opp_repo = OpportunitiesRepository(self._connection())
        opp_repo.soft_delete(opp_id)
