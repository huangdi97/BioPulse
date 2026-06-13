from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/v1/agent", tags=["agent-insights"])


@router.get("/insights")
async def get_insights(page: str = Query(...), user_id: str = Query("default")):
    return {"page_id": page, "insights": [], "count": 0}
