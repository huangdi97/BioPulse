from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from cloud.app.services.recommend_service import RecommendService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/recommend", tags=["Recommendation Engine"])


class ProfileCreate(BaseModel):
    user_id: int
    persona_type: str = ""
    specialization: str = ""
    experience_level: str = "mid"
    preferred_content_types: list[str] = []
    custom_tags: list[str] = []


class ProfileUpdate(BaseModel):
    persona_type: Optional[str] = None
    specialization: Optional[str] = None
    experience_level: Optional[str] = None
    preferred_content_types: Optional[list[str]] = None
    custom_tags: Optional[list[str]] = None


class BehaviorLog(BaseModel):
    user_id: int
    action_type: str
    target_type: str = ""
    target_id: str = ""
    metadata: dict = {}
    session_id: str = ""
    duration_seconds: int = 0


class RecGenerate(BaseModel):
    user_id: int
    rec_types: list[str] = ["content", "strategy", "action"]
    limit: int = 5


@router.post("/profile/create")
def create_profile(
    body: ProfileCreate,
    current_user: dict = Depends(require_scope("visit")),
    service: RecommendService = Depends(),
):
    row = service.create_profile(
        body.user_id,
        body.persona_type,
        body.specialization,
        body.experience_level,
        body.preferred_content_types,
        body.custom_tags,
    )
    return success(data=row)


@router.get("/profile/{user_id}")
def get_profile(
    user_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: RecommendService = Depends(),
):
    return success(data=service.get_profile(user_id))


@router.patch("/profile/{user_id}")
def update_profile(
    user_id: int,
    body: ProfileUpdate,
    current_user: dict = Depends(require_scope("visit")),
    service: RecommendService = Depends(),
):
    row = service.update_profile(
        user_id,
        body.persona_type,
        body.specialization,
        body.experience_level,
        body.preferred_content_types,
        body.custom_tags,
    )
    return success(data=row)


@router.post("/behavior/log")
def log_behavior(
    body: BehaviorLog,
    current_user: dict = Depends(require_scope("visit")),
    service: RecommendService = Depends(),
):
    row = service.log_behavior(
        body.user_id,
        body.action_type,
        body.target_type,
        body.target_id,
        body.metadata,
        body.session_id,
        body.duration_seconds,
    )
    return success(data=row)


@router.get("/behavior/history")
def behavior_history(
    user_id: Optional[int] = Query(None),
    action_type: Optional[str] = Query(None),
    target_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_scope("visit")),
    service: RecommendService = Depends(),
):
    return success(
        data=service.behavior_history(
            user_id=user_id,
            action_type=action_type,
            target_type=target_type,
            limit=limit,
            offset=offset,
        )
    )


@router.post("/generate")
def generate_recommendations(
    body: RecGenerate,
    current_user: dict = Depends(require_scope("visit")),
    service: RecommendService = Depends(),
):
    results = service.generate_recommendations(body.user_id, body.rec_types, body.limit)
    return success(data=results)


@router.get("/list")
def list_recommendations(
    user_id: Optional[int] = Query(None),
    rec_type: Optional[str] = Query(None),
    clicked: Optional[int] = Query(None),
    dismissed: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_scope("visit")),
    service: RecommendService = Depends(),
):
    return success(
        data=service.list_recommendations(
            user_id=user_id,
            rec_type=rec_type,
            clicked=clicked,
            dismissed=dismissed,
            limit=limit,
            offset=offset,
        )
    )


@router.post("/{rec_id}/click")
def mark_clicked(
    rec_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: RecommendService = Depends(),
):
    service.mark_clicked(rec_id)
    return success()


@router.post("/{rec_id}/dismiss")
def mark_dismissed(
    rec_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: RecommendService = Depends(),
):
    service.mark_dismissed(rec_id)
    return success()


@router.get("/dashboard")
def dashboard(
    current_user: dict = Depends(require_scope("visit")),
    service: RecommendService = Depends(),
):
    return success(data=service.dashboard())
