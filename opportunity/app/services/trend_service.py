"""趋势分析服务，用于分析市场数据和行业趋势。"""

import json
import urllib.request
from datetime import datetime, timezone

from opportunity.app.repositories import (
    ResearchTrailRepository,
    TrendAnalysisRepository,
)
from shared.app_settings import settings
from shared.base_service import BaseService

AI_GATEWAY_URL = f"{settings.cloud_api_base}/ai/chat"


"""趋势分析服务，按研究主题聚合数据并通过LLM预测科研趋势。"""


class TrendService(BaseService):
    """趋势分析：按主题聚合时间序列数据、调用LLM预测趋势、保存分析历史。"""

    def _call_llm(self, auth_header: str, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        req_body = {
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 2048,
        }
        req = urllib.request.Request(
            AI_GATEWAY_URL,
            data=json.dumps(req_body).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": auth_header},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
        envelope = json.loads(raw)
        data = envelope.get("data", {})
        return data.get("reply", "") if isinstance(data, dict) else str(data)

    def _aggregate_topic_data(self, topic: str, period: str = "monthly") -> tuple:
        if period == "monthly":
            fmt = "%Y-%m"
        elif period == "quarterly":
            fmt = "%Y-%q"
        elif period == "yearly":
            fmt = "%Y"
        else:
            fmt = "%Y-%m"
        (f"'%{fmt.replace('%Y', 'Y').replace('%m', 'm').replace('%q', 'Q')}'")
        rows = (
            ResearchTrailRepository(self._connection())
            .db.execute(
                f"SELECT strftime('{fmt}', pub_date) as period, COUNT(*) as cnt "
                f"FROM research_trail WHERE topic LIKE ? AND is_active=1 "
                f"GROUP BY period ORDER BY period",
                (f"%{topic}%",),
            )
            .fetchall()
        )
        data_points = [{"period": r["period"], "count": r["cnt"]} for r in rows]
        total = sum(p["count"] for p in data_points)
        return data_points, total

    def get_trends_by_topic(self, topic: str, period: str = "monthly") -> dict:
        """按主题聚合时间序列趋势数据。

        Args:
            topic: 研究主题; period: 聚合周期（monthly/quarterly/yearly）

        Returns:
            dict: 包含 topic、period、data_points、total 的趋势数据
        """
        data_points, total = self._aggregate_topic_data(topic, period)
        return {
            "topic": topic,
            "period": period,
            "data_points": data_points,
            "total": total,
        }

    def predict_trend(self, body, auth_header: str, user_id: int) -> dict:
        """基于历史数据通过LLM预测研究主题的未来趋势。

        Args:
            body: 包含 topic 和 context 的请求体; auth_header: 认证头; user_id: 用户ID

        Returns:
            dict: 包含 prediction、confidence、driving_factors、similar_topics 的预测结果
        """
        data_points, total = self._aggregate_topic_data(body.topic, "monthly")
        months_data = data_points[-12:] if len(data_points) > 12 else data_points
        data_summary = json.dumps(months_data, ensure_ascii=False)
        prompt = f"""研究主题: {body.topic}
过去的数据点（月数: {len(months_data)}）: {data_summary}
"""
        if body.context:
            prompt += f"\n额外背景: {body.context}"
        prompt += """\n请基于以上数据预测该研究主题的趋势，返回JSON格式:
{"prediction": "对未来趋势的预测描述", "confidence": "high/medium/low", "driving_factors": ["因素1", "因素2"], "similar_topics": ["主题1", "主题2"]}"""
        reply = self._call_llm(auth_header, prompt)
        try:
            parsed = json.loads(reply)
        except (json.JSONDecodeError, TypeError):
            parsed = {
                "prediction": reply[:200],
                "confidence": "medium",
                "driving_factors": [],
                "similar_topics": [],
            }
        now = datetime.now(timezone.utc).isoformat()
        TrendAnalysisRepository(self._connection()).create(
            {
                "topic": body.topic,
                "analysis_type": "prediction",
                "period": "monthly",
                "data_summary": data_summary,
                "result": json.dumps(parsed, ensure_ascii=False),
                "confidence": parsed.get("confidence", "medium"),
                "analyzed_at": now,
                "created_by": user_id,
                "created_at": now,
            }
        )
        return {
            "topic": body.topic,
            "prediction": parsed.get("prediction", ""),
            "confidence": parsed.get("confidence", "medium"),
            "driving_factors": parsed.get("driving_factors", []),
            "similar_topics": parsed.get("similar_topics", []),
            "data_points_months": len(months_data),
        }

    def list_history(self, page: int, page_size: int) -> tuple:
        """分页查询趋势分析历史记录。

        Args:
            page: 页码; page_size: 每页条数

        Returns:
            tuple: (items, total, page, page_size, total_pages)
        """
        repo = TrendAnalysisRepository(self._connection())
        return repo.paginate(page=page, page_size=page_size, order_by="analyzed_at DESC")
