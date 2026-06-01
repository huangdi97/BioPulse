from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status

from sales_assistant.app.services.coach_service import CoachService
from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(tags=["coach"])


class PromptCreate(BaseModel):
    trigger_type: Optional[str] = None
    trigger_keywords: Optional[str] = None
    scenario: Optional[str] = None
    prompt_template: Optional[str] = None
    priority: Optional[int] = 5
    category: Optional[str] = None


class PromptUpdate(BaseModel):
    trigger_type: Optional[str] = None
    trigger_keywords: Optional[str] = None
    scenario: Optional[str] = None
    prompt_template: Optional[str] = None
    priority: Optional[int] = None
    category: Optional[str] = None


class SuggestRequest(BaseModel):
    scenario: str
    hcp_name: Optional[str] = None
    product_name: Optional[str] = None
    recent_context: Optional[str] = None
    hcp_tier: Optional[str] = None


class SessionCreate(BaseModel):
    schedule_id: Optional[int] = None
    hcp_name: Optional[str] = None
    current_scenario: Optional[str] = None
    notes: Optional[str] = None


class SessionUpdate(BaseModel):
    status: Optional[str] = None
    ended_at: Optional[str] = None
    notes: Optional[str] = None


@router.post("/coach/prompts")
def create_prompt(
    body: PromptCreate,
    service: CoachService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    user_id = int(current_user["sub"])
    row_id = service.create_prompt(body, user_id)
    return JSONResponse(
        content=success(data={"id": row_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/coach/prompts")
def list_prompts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    scenario: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    service: CoachService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse]:
    total, total_pages, rows = service.list_prompts(page, page_size, scenario, category)
    items = [dict(r) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.patch("/coach/prompts/{prompt_id}")
def update_prompt(
    prompt_id: int,
    body: PromptUpdate,
    service: CoachService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    row = service.update_prompt(prompt_id, body)
    return success(data=row)


@router.delete("/coach/prompts/{prompt_id}")
def delete_prompt(
    prompt_id: int,
    service: CoachService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    service.delete_prompt(prompt_id)
    return success(message="deleted")


@router.post("/coach/suggest")
def coach_suggest(
    body: SuggestRequest,
    service: CoachService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    result = service.coach_suggest(body)
    return success(data=result)


@router.post("/coach/sessions")
def create_session(
    body: SessionCreate,
    service: CoachService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    user_id = int(current_user["sub"])
    row_id = service.create_session(body, user_id)
    return JSONResponse(
        content=success(data={"id": row_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/coach/sessions")
def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: CoachService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse]:
    total, total_pages, rows = service.list_sessions(page, page_size)
    items = [dict(r) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.patch("/coach/sessions/{session_id}")
def update_session(
    session_id: int,
    body: SessionUpdate,
    service: CoachService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    row = service.update_session(session_id, body)
    return success(data=row)
