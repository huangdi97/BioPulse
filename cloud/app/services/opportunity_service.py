"""销售机会服务，负责机会的增删改查、阶段流转与销售漏斗分析。"""

from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import CustomersRepository, OpportunitiesRepository
from cloud.app.services.base import BaseService
from cloud.app.services.opportunity_analysis import VALID_STAGES, OpportunityAnalysisMixin
from shared.base import validate_columns
from shared.columns import TABLE_OPPORTUNITIES_COLS


class OpportunityService(OpportunityAnalysisMixin, BaseService):
    """销售机会服务，提供机会的增删改查、阶段流转与销售漏斗分析。"""

    def _get_opp_or_404(self, opp_id: int) -> dict:
        """按 ID 获取活跃机会，不存在则抛出 404。

        Args:
            opp_id: 机会 ID

        Returns:
            机会记录字典

        Raises:
            HTTPException: 机会不存在时返回 404
        """
        opp_repo = OpportunitiesRepository(self.db)
        rows = opp_repo.list_all(
            conditions=["id=?", "is_active=1"],
            params=[opp_id],
        )
        if not rows:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
        return rows[0]

    def _row_to_dict(self, row) -> dict:
        """将数据库行转为含客户名称的字典。

        Args:
            row: 数据库行或字典

        Returns:
            含 customer_name 的完整机会字典
        """
        cust_repo = CustomersRepository(self.db)
        customer = cust_repo.get_by_id(row["customer_id"])
        return {
            "id": row["id"],
            "customer_id": row["customer_id"],
            "customer_name": customer["name"] if customer else "",
            "name": row["name"],
            "description": row["description"],
            "stage": row["stage"],
            "probability": row["probability"],
            "estimated_value": row["estimated_value"],
            "actual_value": row["actual_value"],
            "assigned_to": row["assigned_to"],
            "close_date": row["close_date"],
            "notes": row["notes"],
            "is_active": row["is_active"],
            "created_by": row["created_by"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

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
        """创建一个新的销售机会。

        Args:
            customer_id: 关联的客户 ID
            name: 机会名称
            description: 机会描述
            stage: 初始阶段 (lead/qualify/proposal/negotiation/won/lost)
            estimated_value: 预估价值
            actual_value: 实际价值
            assigned_to: 可选，指派负责人 ID
            close_date: 可选，预计关闭日期
            notes: 备注
            user_id: 创建者用户 ID

        Returns:
            新创建的机会记录字典（含客户名称）

        Raises:
            HTTPException: 客户不存在或无效阶段时抛出
        """
        cust_repo = CustomersRepository(self.db)
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

        opp_repo = OpportunitiesRepository(self.db)
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
        return self._row_to_dict(row)

    def list_opportunities(
        self,
        stage: Optional[str] = None,
        assigned_to: Optional[int] = None,
        customer_id: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """分页查询销售机会列表。

        Args:
            stage: 可选，按阶段过滤
            assigned_to: 可选，按负责人 ID 过滤
            customer_id: 可选，按客户 ID 过滤
            search: 可选，按名称或描述模糊搜索
            page: 页码，默认 1
            page_size: 每页条数，默认 20

        Returns:
            包含 items、total、page、page_size 的字典
        """
        opp_repo = OpportunitiesRepository(self.db)
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
            "items": [self._row_to_dict(r) for r in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_opportunity(self, opp_id: int) -> dict:
        """获取单个销售机会详情。

        Args:
            opp_id: 机会 ID

        Returns:
            机会记录字典（含客户名称）

        Raises:
            HTTPException: 机会不存在时返回 404
        """
        row = self._get_opp_or_404(opp_id)
        return self._row_to_dict(row)

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
        """更新销售机会的指定字段。

        Args:
            opp_id: 机会 ID
            name: 可选，新机会名称
            description: 可选，新描述
            stage: 可选，新阶段，变更时会重新计算概率并校验阶段流转合法性
            estimated_value: 可选，新预估价值
            actual_value: 可选，新实际价值
            assigned_to: 可选，新负责人 ID
            close_date: 可选，新预计关闭日期
            notes: 可选，新备注

        Returns:
            更新后的机会记录字典

        Raises:
            HTTPException: 机会不存在、阶段无效或从终态流转时抛出
        """
        self._get_opp_or_404(opp_id)

        opp_repo = OpportunitiesRepository(self.db)
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

        row = self._get_opp_or_404(opp_id)
        return self._row_to_dict(row)

    def delete_opportunity(self, opp_id: int) -> None:
        """软删除一个销售机会。

        Args:
            opp_id: 机会 ID

        Raises:
            HTTPException: 机会不存在时返回 404
        """
        self._get_opp_or_404(opp_id)
        opp_repo = OpportunitiesRepository(self.db)
        opp_repo.soft_delete(opp_id)
