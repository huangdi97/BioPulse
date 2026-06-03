from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from sales_assistant.app.services.funnel_service import FunnelService
from shared.auth import get_current_user
from shared.base import ApiResponse, success

router = APIRouter(tags=["Funnel Analysis"])


class EventTypeStats(BaseModel):
    total: int
    completed: int


class FunnelData(BaseModel):
    total_schedules: int
    completed_schedules: int
    completion_rate: float
    with_notes: int
    note_rate: float
    by_event_type: dict[str, EventTypeStats]


@router.get("/funnel", response_model=ApiResponse[FunnelData])
def funnel_analysis(
    service: FunnelService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> Any:
    """funnel analysis。"""
    data = service.funnel_analysis()
    return success(
        FunnelData(
            total_schedules=data["total_schedules"],
            completed_schedules=data["completed_schedules"],
            completion_rate=data["completion_rate"],
            with_notes=data["with_notes"],
            note_rate=data["note_rate"],
            by_event_type={k: EventTypeStats(total=v["total"], completed=v["completed"]) for k, v in data["by_event_type"].items()},
        )
    )
