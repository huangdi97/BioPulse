from fastapi import APIRouter, Query

from cloud.app.services.agent_insight_service import AgentInsightService

router = APIRouter(prefix="/api/v1/agent", tags=["agent-insights"])

_insight_service = AgentInsightService()


@router.get("/insights")
async def get_insights(page: str = Query(...), user_id: str = Query("default")):
    insights = await _insight_service.get_insights(page, user_id)
    return {"page_id": page, "insights": [i.model_dump() for i in insights], "count": len(insights)}
