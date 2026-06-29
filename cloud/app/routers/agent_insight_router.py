from fastapi import APIRouter, Query
from pydantic import BaseModel

from cloud.app.agent_runtime.core.models import Insight
from cloud.app.services.agent_ops.agent_insight_service import AgentInsightService

router = APIRouter(prefix="/api/v1/agent", tags=["agent-insights"])

_insight_service = AgentInsightService()


class AgentInsightResponse(BaseModel):
    page_id: str
    insights: list[Insight]
    count: int


@router.get("/insights", response_model=AgentInsightResponse)
async def get_insights(page: str = Query(...), user_id: str = Query("default")):
    """获取指定页面的智能体洞察列表。

    请求示例:
        GET /api/v1/agent/insights?page=manager_dashboard&user_id=user_001

    响应示例:
        {
          "page_id": "manager_dashboard",
          "insights": [
            {
              "agent_key": "anomaly_analysis",
              "page_id": "manager_dashboard",
              "summary": "发现 3 条异常拜访记录",
              "details": {"risk_level": "high", "records": [...]},
              "confidence": 0.87
            }
          ],
          "count": 1
        }
    """
    insights = await _insight_service.get_insights(page, user_id)
    return AgentInsightResponse(page_id=page, insights=insights, count=len(insights))
