"""BD Pipeline API 路由。"""

from __future__ import annotations

import sqlite3
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from starlette import status

from cloud.app.bd_pipeline import BDDashboardAggregator, BDPipelineService, LeadScorer
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/api/bd", tags=["BD管线"])

_db = sqlite3.connect(":memory:", check_same_thread=False)
_pipeline = BDPipelineService(_db)
_scorer = LeadScorer()
_dashboard = BDDashboardAggregator(_pipeline)


class PipelineCreateRequest(BaseModel):
    lead_id: str
    lead_name: str
    company: str = ""
    amount: float = 0.0
    probability: float = 0.0
    owner: str = ""
    score: float = 0.0
    tier: str = "cold"
    notes: str = ""
    bant: dict[str, float] = {}
    custom: dict[str, float] = {}


class PipelineUpdateRequest(BaseModel):
    stage: str
    amount: Optional[float] = None
    probability: Optional[float] = None
    notes: Optional[str] = None


@router.get("/pipeline", tags=["BD管线"])
async def list_pipeline(stage: str = Query(""), owner: str = Query("")) -> list[dict[str, Any]]:
    """查看BD管线。"""
    return success(data=_pipeline.list_all(stage=stage or None, owner=owner or None))


@router.post("/pipeline", status_code=status.HTTP_201_CREATED, tags=["BD管线"])
async def create_pipeline(req: PipelineCreateRequest, _: dict = Depends(require_scope("visit"))) -> dict[str, Any]:
    """新增线索到BD管线。"""
    score_result = _scorer.score(req.lead_id, req.bant, req.custom)
    entry = _pipeline.create(
        lead_id=req.lead_id,
        lead_name=req.lead_name,
        company=req.company,
        amount=req.amount,
        probability=req.probability,
        owner=req.owner,
        score=score_result.total_score,
        tier=score_result.tier,
        notes=req.notes,
    )
    return success(
        data={
            "pipeline": entry,
            "score": {
                "total": score_result.total_score,
                "tier": score_result.tier,
                "bant": score_result.bant_score,
                "custom": score_result.custom_score,
            },
        }
    )


@router.put("/pipeline/{lead_id}", tags=["BD管线"])
async def update_pipeline_stage(lead_id: str, req: PipelineUpdateRequest, _: dict = Depends(require_scope("visit"))) -> dict[str, Any]:
    """更新管线阶段。"""
    result = _pipeline.update_stage(lead_id, req.stage, req.amount, req.probability, req.notes)
    if not result:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Lead {lead_id} not found")
    return success(data={"pipeline": result})


@router.get("/dashboard", tags=["BD管线"])
async def bd_dashboard() -> dict[str, Any]:
    """BD看板数据。"""
    return success(data=_dashboard.overview())
