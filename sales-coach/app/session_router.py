"""会话路由模块，提供教练会话的创建、查询、对话记录管理及删除接口。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status

from sales_coach.app.services.session_service import SessionService
from shared.auth_scope import require_scope
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(tags=["sessions"])


class SessionCreate(BaseModel):
    """Request model for creating a coach session."""

    trainee_name: Optional[str] = None
    score: Optional[int] = None
    feedback: Optional[str] = None
    strengths: Optional[str] = None
    improvements: Optional[str] = None
    session_date: Optional[str] = None
    session_type: Optional[str] = "roleplay"
    scenario_id: Optional[int] = None
    role: Optional[str] = None


class SessionUpdate(BaseModel):
    """Request model for updating a coach session."""

    trainee_name: Optional[str] = None
    score: Optional[int] = None
    feedback: Optional[str] = None
    strengths: Optional[str] = None
    improvements: Optional[str] = None
    session_date: Optional[str] = None
    session_type: Optional[str] = None
    scenario_id: Optional[int] = None
    dialogue_log: Optional[str] = None
    role: Optional[str] = None
    compliance_violations: Optional[int] = None
    auto_assessment: Optional[str] = None
    reflection_report: Optional[str] = None


class SessionOut(BaseModel):
    """Response model for a coach session."""

    id: int
    module_id: int
    trainee_name: Optional[str] = None
    score: Optional[int] = None
    feedback: Optional[str] = None
    strengths: Optional[str] = None
    improvements: Optional[str] = None
    session_date: Optional[str] = None
    session_type: Optional[str] = "roleplay"
    scenario_id: Optional[int] = None
    dialogue_log: Optional[str] = None
    role: Optional[str] = None
    compliance_violations: Optional[int] = 0
    auto_assessment: Optional[str] = None
    reflection_report: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[str] = None


@router.post("/modules/{module_id}/sessions", summary="创建会话", description="为培训模块创建新的教练会话", tags=["陪练"])
def create_session(
    module_id: int,
    body: SessionCreate,
    service: SessionService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """Create a coach session for a training module."""
    user_id = int(current_user["sub"])
    if body.session_type and body.session_type != "roleplay":
        result = service.create_digital_human_session(
            module_id,
            body,
            user_id,
            session_type=body.session_type,
            scenario_id=body.scenario_id,
            role=body.role,
        )
    else:
        result = service.create(module_id, body, user_id)
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/modules/{module_id}/sessions", summary="会话列表", description="分页查询培训模块的教练会话列表", tags=["陪练"])
def list_sessions(
    module_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: SessionService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[PaginatedResponse[SessionOut]]:
    """List coach sessions for a training module."""
    total, total_pages, rows = service.list(module_id, page, page_size)
    items = [SessionOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/sessions", summary="全部会话", description="获取所有教练会话列表", tags=["陪练"])
def list_all_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ApiResponse[PaginatedResponse[SessionOut]]:
    """List all coach sessions."""
    return success(
        data=PaginatedResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=0,
        )
    )


@router.get("/sessions/{session_id}", summary="会话详情", description="根据ID获取教练会话详情", tags=["陪练"])
def get_session(
    session_id: int,
    service: SessionService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[SessionOut]:
    """Get a single coach session by ID."""
    row = service.get(session_id)
    return success(data=SessionOut(**row))


@router.get("/sessions/{session_id}/dialogue", summary="对话历史", description="获取教练会话的完整对话历史记录", tags=["陪练"])
def get_session_dialogue(
    session_id: int,
    service: SessionService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """Get the full dialogue history for a coach session."""
    history = service.get_dialogue_history(session_id)
    return success(data={"session_id": session_id, "dialogue": history})


@router.post("/sessions/{session_id}/dialogue", summary="追加对话", description="向教练会话日志中追加对话条目", tags=["陪练"])
def append_dialogue(
    session_id: int,
    entry: dict,
    service: SessionService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[SessionOut]:
    """Append a dialogue entry to a coach session log."""
    updated = service.update_dialogue_log(session_id, entry)
    return success(data=SessionOut(**updated))


@router.patch("/sessions/{session_id}", summary="更新会话", description="更新教练会话信息", tags=["陪练"])
def update_session(
    session_id: int,
    body: SessionUpdate,
    service: SessionService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[SessionOut]:
    """Update a coach session."""
    updated = service.update(session_id, body)
    return success(data=SessionOut(**updated))


@router.delete("/sessions/{session_id}", summary="删除会话", description="删除指定的教练会话记录", tags=["陪练"])
def delete_session(
    session_id: int,
    service: SessionService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """Delete a coach session."""
    service.delete(session_id)
    return success(message="deleted")
