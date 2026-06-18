"""策略服务：AI生成与模拟销售策略。"""

import json
import logging
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException
from starlette import status

from sales_assistant.app.repositories import StrategyRepository
from shared.ai_gateway import TIMEOUT_SECONDS
from shared.app_settings import settings
from shared.base_service import BaseService

AI_GATEWAY_URL = f"{settings.cloud_api_base}/ai/chat"
logger = logging.getLogger(__name__)


class StrategyService(BaseService):
    """策略服务：生成销售策略、模拟策略有效性、策略对比分析。"""

    def create_strategy(self, body, user_id: int) -> int:
        """创建销售策略。

        Args:
            body: 策略请求体，包含策略信息。
            user_id: 创建者用户ID。

        Returns:
            新创建的策略ID。
        """
        now = datetime.now(timezone.utc).isoformat()
        repo = StrategyRepository(self._connection())
        return repo.create(
            body.model_dump(),
            extra={"created_by": user_id, "created_at": now, "updated_at": now},
        )

    def list_strategies(
        self,
        page: int,
        page_size: int,
        hcp_name: Optional[str] = None,
        status_val: Optional[str] = None,
        goal: Optional[str] = None,
    ) -> tuple:
        """分页查询策略列表。

        Args:
            page: 页码。
            page_size: 每页条数。
            hcp_name: 按客户名称模糊筛选。
            status_val: 按状态筛选。
            goal: 按目标筛选。

        Returns:
            (记录列表, 总条数) 元组。
        """
        conditions: List[str] = ["is_active = 1"]
        params: list = []
        if hcp_name:
            conditions.append("hcp_name LIKE ?")
            params.append(f"%{hcp_name}%")
        if status_val:
            conditions.append("status LIKE ?")
            params.append(f"%{status_val}%")
        if goal:
            conditions.append("goal LIKE ?")
            params.append(f"%{goal}%")
        repo = StrategyRepository(self._connection())
        return repo.paginate(page, page_size, conditions, params, "created_at DESC")

    def get_strategy(self, strategy_id: int) -> dict:
        """获取单个策略详情。

        Args:
            strategy_id: 策略ID。

        Returns:
            策略详情字典，不存在或已删除则抛404。
        """
        repo = StrategyRepository(self._connection())
        row = repo.get_by_id(strategy_id)
        if not row or row["is_active"] != 1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found",
            )
        return dict(row)

    def update_strategy(self, strategy_id: int, body) -> dict:
        """更新策略。

        Args:
            strategy_id: 策略ID。
            body: 更新数据。

        Returns:
            更新后的策略详情字典。
        """
        repo = StrategyRepository(self._connection())
        row = repo.get_by_id(strategy_id)
        if not row or row["is_active"] != 1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found",
            )
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(strategy_id, updates)
        return dict(repo.get_by_id(strategy_id))

    def delete_strategy(self, strategy_id: int) -> None:
        """软删除策略。

        Args:
            strategy_id: 策略ID。
        """
        repo = StrategyRepository(self._connection())
        row = repo.get_by_id(strategy_id)
        if not row or not row["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found",
            )
        repo.soft_delete(strategy_id)

    def generate_strategy(self, body, user_id: int) -> dict:
        """调用AI生成销售策略并保存。

        Args:
            body: 策略生成请求体，含客户名称、目标等。
            user_id: 创建者用户ID。

        Returns:
            生成的策略详情字典。
        """
        now = datetime.now(timezone.utc).isoformat()
        user_text = f"客户：{body.hcp_name}，目标：{body.goal}"
        if body.hcp_tier:
            user_text += f"，级别：{body.hcp_tier}"
        if body.product_name:
            user_text += f"，产品：{body.product_name}"
        sp = '生成策略：回复JSON {"approach":"...","talking_points":"...","expected_outcome":"..."}'
        try:
            req = urllib.request.Request(
                AI_GATEWAY_URL,
                data=json.dumps(
                    {
                        "messages": [
                            {"role": "system", "content": sp},
                            {"role": "user", "content": user_text},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 2048,
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                reply = json.loads(resp.read()).get("data", {}).get("reply", "")
            parsed = json.loads(reply) if reply else {}
        except Exception:
            logger.exception("Strategy service parse异常")
            parsed = {}
        repo = StrategyRepository(self._connection())
        strategy_id = repo.create(
            {
                "hcp_name": body.hcp_name,
                "goal": body.goal,
                "approach": parsed.get("approach", ""),
                "talking_points": parsed.get("talking_points", ""),
                "expected_outcome": parsed.get("expected_outcome", ""),
            },
            extra={"created_by": user_id, "created_at": now, "updated_at": now},
        )
        return dict(repo.get_by_id(strategy_id))

    def compare_strategies(self, ids: str) -> list:
        """批量对比多个策略。

        Args:
            ids: 逗号分隔的策略ID字符串。

        Returns:
            策略详情列表。
        """
        id_list = [int(x.strip()) for x in ids.split(",") if x.strip()]
        if not id_list:
            raise HTTPException(status_code=400, detail="Provide at least one strategy id")
        repo = StrategyRepository(self._connection())
        conditions = [f"id IN ({','.join('?' * len(id_list))})", "is_active = 1"]
        rows = repo.list_all(conditions, id_list)
        if not rows:
            raise HTTPException(status_code=404, detail="No strategies found")
        return [dict(r) for r in rows]

    def simulate_strategy(self, body) -> dict:
        """模拟预测策略有效性。

        Args:
            body: 模拟请求，含客户名称、策略方法、产品名称等。

        Returns:
            包含预测有效性、置信度和相似案例数的字典。
        """
        similar = self.db.execute(
            "SELECT COUNT(*) AS cnt, COALESCE(AVG(CAST(effectiveness AS REAL)), 0) AS avg_eff "
            "FROM strategy_simulation WHERE approach LIKE ? AND effectiveness IS NOT NULL",
            (f"%{body.approach}%",),
        ).fetchone()
        similar_cnt = int(similar["cnt"])
        similar_avg_eff = float(similar["avg_eff"])
        user_text = f"客户：{body.hcp_name}，策略：{body.approach}"
        if body.product_name:
            user_text += f"，产品：{body.product_name}"
        user_text += '。预测此策略有效性（0-1）并给出置信度（高/中/低），回复JSON：{"effectiveness":0.7,"confidence":"中"}'
        try:
            req = urllib.request.Request(
                AI_GATEWAY_URL,
                data=json.dumps(
                    {
                        "messages": [
                            {"role": "system", "content": "你是一位策略分析师。"},
                            {"role": "user", "content": user_text},
                        ],
                        "temperature": 0.5,
                        "max_tokens": 512,
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                reply = json.loads(resp.read()).get("data", {}).get("reply", "")
            ai = json.loads(reply) if reply else {}
            predicted = float(ai.get("effectiveness", similar_avg_eff or 0.5))
            confidence = ai.get("confidence", "中")
        except Exception:
            logger.exception("Strategy service predict异常")
            predicted = similar_avg_eff or 0.5
            confidence = "低"
        return {
            "predicted_effectiveness": round(predicted, 2),
            "confidence": confidence,
            "similar_cases": similar_cnt,
        }
