"""数字人路由模块，提供数字人会话创建、消息交互、难度调整及技能迁移接口。"""

from typing import Optional

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status

from sales_coach.app.services.digital_human_difficulty_service import DigitalHumanDifficultyService
from sales_coach.app.services.digital_human_memory_service import DigitalHumanMemoryService
from sales_coach.app.services.digital_human_service import DigitalHumanService
from shared.app_settings import settings as app_settings
from shared.auth_scope import require_scope
from shared.base import success
from shared.config import settings

router = APIRouter(prefix="/coach/digital-human", tags=["Digital Human Coach"])


class SessionCreate(BaseModel):
    """SessionCreate 服务类。"""

    scenario_id: int
    module_id: int = 0
    role: str = "doctor"


class MessageSend(BaseModel):
    """MessageSend 服务类。"""

    content: str
    ai_gateway_url: str = f"{app_settings.cloud_api_base}/ai/gateway"


@router.post("/sessions", summary="创建会话", description="创建新的数字人会话")
def create_session(
    body: SessionCreate,
    service: DigitalHumanService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """创建会话。

    Args:
        service: 描述
        current_user: 描述

    Returns:
        描述
    """
    user_id = int(current_user["sub"])
    result = service.create_session(
        body.scenario_id,
        body.module_id,
        body.role,
        user_id,
    )
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.post("/sessions/{session_id}/message", summary="发送消息", description="向数字人发送消息并获取回复")
def send_message(
    session_id: int,
    body: MessageSend,
    service: DigitalHumanService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """发送消息。

    Args:
        session_id: 描述
        service: 描述
        current_user: 描述

    Returns:
        描述
    """
    user_id = int(current_user["sub"])
    result = service.send_message(
        session_id,
        body.content,
        body.ai_gateway_url,
        user_id,
    )
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@router.get("/sessions/{session_id}", summary="会话详情", description="获取数字人会话详情")
def get_session(
    session_id: int,
    service: DigitalHumanService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """获取会话。

    Args:
        session_id: 描述
        service: 描述
        current_user: 描述

    Returns:
        描述
    """
    result = service.get_session(session_id)
    return success(data=result)


@router.post("/sessions/{session_id}/adjust-difficulty", summary="调整难度", description="动态调整数字人会话的难度")
def adjust_difficulty(
    session_id: int,
    service: DigitalHumanDifficultyService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """调整难度。

    Args:
        session_id: 描述
        service: 描述
        current_user: 描述

    Returns:
        描述
    """
    result = service.adjust_difficulty(session_id)
    return success(data=result)


@router.post("/sessions/{session_id}/end", summary="结束会话", description="结束当前数字人会话")
def end_session(
    session_id: int,
    service: DigitalHumanService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """结束会话。

    Args:
        session_id: 描述
        service: 描述
        current_user: 描述

    Returns:
        描述
    """
    user_id = int(current_user["sub"])
    result = service.end_session(session_id, user_id)
    return success(data=result)


@router.get("/sessions", summary="会话列表", description="获取当前用户的数字人会话列表")
def list_sessions(
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    service: DigitalHumanService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """获取会话列表。

    Args:
        status: 描述
        limit: 描述
        service: 描述
        current_user: 描述

    Returns:
        描述
    """
    user_id = int(current_user["sub"])
    result = service.list_sessions(user_id=user_id, status=status, limit=limit)
    return success(data={"sessions": result, "total": len(result)})


@router.post("/sessions/{session_id}/save-memory", summary="保存记忆", description="保存数字人训练记忆数据")
def save_training_memory(
    session_id: int = Path(..., description="Session ID"),
    service: DigitalHumanMemoryService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """保存训练记忆。

    Args:
        session_id: 描述
        service: 描述
        current_user: 描述

    Returns:
        描述
    """
    result = service.save_training_memory(session_id)
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@router.get("/benchmarks", summary="基准数据", description="获取基准评分数据")
def get_benchmarks(
    service: DigitalHumanMemoryService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """获取基准数据。

    Args:
        service: 描述
        current_user: 描述

    Returns:
        描述
    """
    result = service.get_benchmarks()
    return success(data=result)


@router.get("/sessions/{session_id}/benchmark", summary="基准对比", description="将会话数据与基准数据进行对比分析")
def get_session_benchmark(
    session_id: int = Path(..., description="Session ID"),
    service: DigitalHumanMemoryService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """get_session_benchmark 操作。

    Args:
        session_id: 描述
        service: 描述
        current_user: 描述

    Returns:
        描述
    """
    result = service.compare_with_benchmark(session_id)
    return success(data=result)


@router.post("/sessions/{from_id}/transfer-to/{to_id}", summary="迁移技能", description="将会话中学到的技能迁移至目标会话")
def transfer_skills(
    from_id: int = Path(..., description="Source session ID"),
    to_id: int = Path(..., description="Target session ID"),
    service: DigitalHumanMemoryService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """迁移技能。

    Args:
        from_id: 描述
        to_id: 描述
        service: 描述
        current_user: 描述

    Returns:
        描述
    """
    result = service.transfer_skills(from_id, to_id)
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@router.post("/sessions/{session_id}/voice-input", summary="语音输入", description="多模态语音输入接口（预留功能）")
def voice_input(session_id: int, current_user: dict = Depends(require_scope("visit"))):
    return success(
        data={
            "provider": settings.DIGITAL_HUMAN_PROVIDER,
            "status": "not_implemented",
            "message": "多模态语音输入，等待数字人供应商接入",
        }
    )


@router.post("/sessions/{session_id}/video-input", summary="视频输入", description="多模态视频输入接口（预留功能）")
def video_input(session_id: int, current_user: dict = Depends(require_scope("visit"))):
    return success(
        data={
            "provider": settings.DIGITAL_HUMAN_PROVIDER,
            "status": "not_implemented",
            "message": "多模态视频输入，等待数字人供应商接入",
        }
    )
