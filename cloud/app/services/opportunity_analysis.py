"""销售机会分析与阶段流转方法。"""

from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import OpportunitiesRepository
from shared.base import validate_columns
from shared.columns import TABLE_OPPORTUNITIES_COLS

VALID_STAGES = ["lead", "qualify", "proposal", "negotiation", "won", "lost"]

TERMINAL_STAGES = {"won", "lost"}

STAGE_ORDER = ["lead", "qualify", "proposal", "negotiation", "won", "lost"]


class OpportunityAnalysisMixin:
    """销售漏斗分析、阶段概率和阶段流转方法。"""

    def _stage_probability(self, stage: str) -> int:
        """返回指定阶段的成功概率百分比。

        Args:
            stage: 阶段名称

        Returns:
            概率值（0-100）
        """
        mapping = {
            "lead": 10,
            "qualify": 30,
            "proposal": 50,
            "negotiation": 75,
            "won": 100,
            "lost": 0,
        }
        return mapping.get(stage, 0)

    def _validate_stage_transition(self, current: str, target: str) -> None:
        """校验阶段流转合法性，终态不可再流转。

        Args:
            current: 当前阶段
            target: 目标阶段

        Raises:
            HTTPException: 当前阶段为终态时抛出 400
        """
        if current in TERMINAL_STAGES:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Cannot transition from a terminal stage",
            )

    def get_pipeline(self) -> dict:
        """获取销售漏斗数据，按阶段统计机会数量和金额。

        Returns:
            包含 pipeline 列表的字典，每项含 stage、count、total_value
        """
        opp_repo = OpportunitiesRepository(self.db)
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

        opp_repo = OpportunitiesRepository(self.db)
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
