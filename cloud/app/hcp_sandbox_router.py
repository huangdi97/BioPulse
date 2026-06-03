from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from starlette import status

from cloud.app.services.hcp_sandbox_service import HcpSandboxService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/hcp-sandbox", tags=["HCP Sandbox"])


class HcpCreate(BaseModel):
    name: str
    title: str = ""
    hospital: str = ""
    department: str = ""
    specialty: str = ""
    city: str = ""
    tier: str = "B"
    traits: dict = {}
    prescription_volume: float = 0
    influence_score: float = 0.5
    digital_engagement: float = 0.5


class HcpUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    specialty: Optional[str] = None
    city: Optional[str] = None
    tier: Optional[str] = None
    traits: Optional[dict] = None
    prescription_volume: Optional[float] = None
    influence_score: Optional[float] = None
    digital_engagement: Optional[float] = None
    is_active: Optional[int] = None


class InteractionCreate(BaseModel):
    interaction_type: str
    content: str = ""
    response: str = ""
    outcome: str = ""
    strategy_used: str = ""
    conducted_at: Optional[str] = None


class SimulateRequest(BaseModel):
    scenario: str
    strategy: str = ""


@router.post("/profiles", status_code=status.HTTP_201_CREATED)
def create_profile(
    body: HcpCreate,
    current_user: dict = Depends(require_scope("visit")),
    service: HcpSandboxService = Depends(),
):
    """创建一个新的 HCP 档案。

    Args:
        body: HCP 创建请求体。
        current_user: 当前认证用户。
        service: HCP 沙箱服务实例。

    Returns:
        包含新创建档案数据的响应。
    """
    user_id = int(current_user["sub"])
    row = service.create_profile(
        name=body.name,
        title=body.title,
        hospital=body.hospital,
        department=body.department,
        specialty=body.specialty,
        city=body.city,
        tier=body.tier,
        traits=body.traits,
        prescription_volume=body.prescription_volume,
        influence_score=body.influence_score,
        digital_engagement=body.digital_engagement,
        user_id=user_id,
    )
    return success(data=row)


@router.get("/profiles")
def list_profiles(
    tier: Optional[str] = Query(None),
    specialty: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_scope("visit")),
    service: HcpSandboxService = Depends(),
):
    """分页查询 HCP 档案列表。

    Args:
        tier: 等级筛选。
        specialty: 专业筛选。
        city: 城市筛选。
        page: 页码，从1开始。
        page_size: 每页数量。
        current_user: 当前认证用户。
        service: HCP 沙箱服务实例。

    Returns:
        包含档案列表的响应。
    """
    result = service.list_profiles(
        tier=tier,
        specialty=specialty,
        city=city,
        page=page,
        page_size=page_size,
    )
    return success(data=result)


@router.get("/profiles/{hcp_id}")
def get_profile(
    hcp_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: HcpSandboxService = Depends(),
):
    """获取指定 HCP 档案的详情。

    Args:
        hcp_id: HCP ID。
        current_user: 当前认证用户。
        service: HCP 沙箱服务实例。

    Returns:
        包含档案数据的响应。
    """
    row = service.get_profile(hcp_id)
    return success(data=row)


@router.patch("/profiles/{hcp_id}")
def update_profile(
    hcp_id: int,
    body: HcpUpdate,
    current_user: dict = Depends(require_scope("visit")),
    service: HcpSandboxService = Depends(),
):
    """更新指定 HCP 档案的信息。

    Args:
        hcp_id: HCP ID。
        body: HCP 更新请求体。
        current_user: 当前认证用户。
        service: HCP 沙箱服务实例。

    Returns:
        包含更新后档案数据的响应。
    """
    row = service.update_profile(
        hcp_id=hcp_id,
        name=body.name,
        title=body.title,
        hospital=body.hospital,
        department=body.department,
        specialty=body.specialty,
        city=body.city,
        tier=body.tier,
        traits=body.traits,
        prescription_volume=body.prescription_volume,
        influence_score=body.influence_score,
        digital_engagement=body.digital_engagement,
        is_active=body.is_active,
    )
    return success(data=row)


@router.post("/profiles/{hcp_id}/interactions")
def create_interaction(
    hcp_id: int,
    body: InteractionCreate,
    current_user: dict = Depends(require_scope("visit")),
    service: HcpSandboxService = Depends(),
):
    """为指定 HCP 创建一条互动记录。

    Args:
        hcp_id: HCP ID。
        body: 互动创建请求体。
        current_user: 当前认证用户。
        service: HCP 沙箱服务实例。

    Returns:
        包含新互动数据的响应。
    """
    user_id = int(current_user["sub"])
    row = service.create_interaction(
        hcp_id=hcp_id,
        interaction_type=body.interaction_type,
        content=body.content,
        response=body.response,
        outcome=body.outcome,
        strategy_used=body.strategy_used,
        conducted_at=body.conducted_at,
        user_id=user_id,
    )
    return success(data=row)


@router.get("/profiles/{hcp_id}/interactions")
def list_interactions(
    hcp_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_scope("visit")),
    service: HcpSandboxService = Depends(),
):
    """分页查询指定 HCP 的互动记录。

    Args:
        hcp_id: HCP ID。
        page: 页码，从1开始。
        page_size: 每页数量。
        current_user: 当前认证用户。
        service: HCP 沙箱服务实例。

    Returns:
        包含互动列表的响应。
    """
    result = service.list_interactions(
        hcp_id=hcp_id,
        page=page,
        page_size=page_size,
    )
    return success(data=result)


@router.post("/profiles/{hcp_id}/simulate")
def simulate(
    hcp_id: int,
    body: SimulateRequest,
    current_user: dict = Depends(require_scope("visit")),
    service: HcpSandboxService = Depends(),
):
    """对指定 HCP 执行场景模拟。

    Args:
        hcp_id: HCP ID。
        body: 模拟请求体，包含场景和策略。
        current_user: 当前认证用户。
        service: HCP 沙箱服务实例。

    Returns:
        包含模拟结果的响应。
    """
    user_id = int(current_user["sub"])
    row = service.simulate(
        hcp_id=hcp_id,
        scenario=body.scenario,
        strategy=body.strategy,
        user_id=user_id,
    )
    return success(data=row)


@router.get("/simulations")
def list_simulations(
    hcp_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_scope("visit")),
    service: HcpSandboxService = Depends(),
):
    """分页查询模拟记录列表。

    Args:
        hcp_id: HCP ID 筛选。
        status: 状态筛选。
        page: 页码，从1开始。
        page_size: 每页数量。
        current_user: 当前认证用户。
        service: HCP 沙箱服务实例。

    Returns:
        包含模拟列表的响应。
    """
    result = service.list_simulations(
        hcp_id=hcp_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    return success(data=result)


@router.get("/simulations/{sim_id}")
def get_simulation(
    sim_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: HcpSandboxService = Depends(),
):
    """获取指定模拟记录的详情。

    Args:
        sim_id: 模拟 ID。
        current_user: 当前认证用户。
        service: HCP 沙箱服务实例。

    Returns:
        包含模拟数据的响应。
    """
    row = service.get_simulation(sim_id)
    return success(data=row)


@router.get("/dashboard")
def dashboard(
    current_user: dict = Depends(require_scope("visit")),
    service: HcpSandboxService = Depends(),
):
    """获取 HCP 沙箱仪表盘数据。

    Args:
        current_user: 当前认证用户。
        service: HCP 沙箱服务实例。

    Returns:
        包含仪表盘数据的响应。
    """
    result = service.dashboard()
    return success(data=result)
