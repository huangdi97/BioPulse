"""激励规则管理路由。"""

from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from cloud.app.services.operations.incentive_service import IncentiveService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/api/v1/incentives", tags=["incentives"])


class ConfigureRulesRequest(BaseModel):
    name: str
    rule_type: str
    conditions: dict
    reward: dict
    description: Optional[str] = None


class CalculateBonusRequest(BaseModel):
    rule_id: int
    actuals: dict


class SimulateRequest(BaseModel):
    rule_id: int
    hypotheticals: list[dict]


class ApproveRequest(BaseModel):
    rule_id: int
    approver: str


@router.post("/rules")
def configure_rules(
    body: ConfigureRulesRequest,
    _: dict = Depends(require_scope("manager")),
    service: IncentiveService = Depends(),
) -> Any:
    """配置一条新的激励规则。

    Args:
        body: 规则配置参数。
        _: 当前登录用户（manager 权限）。
        service: 激励规则服务。

    Returns:
        新建的激励规则。
    """
    rule = service.configure_rules(
        name=body.name,
        rule_type=body.rule_type,
        conditions=body.conditions,
        reward=body.reward,
        description=body.description,
    )
    return success(data=rule)


@router.post("/calculate")
def calculate_bonus(
    body: CalculateBonusRequest,
    _: dict = Depends(require_scope("manager")),
    service: IncentiveService = Depends(),
) -> Any:
    """根据实际业绩计算应发奖金。

    Args:
        body: 计算请求（规则 ID + 实际业绩）。
        _: 当前登录用户（manager 权限）。
        service: 激励规则服务。

    Returns:
        奖金计算结果。
    """
    result = service.calculate_bonus(rule_id=body.rule_id, actuals=body.actuals)
    return success(data=result)


@router.post("/simulate")
def simulate(
    body: SimulateRequest,
    _: dict = Depends(require_scope("manager")),
    service: IncentiveService = Depends(),
) -> Any:
    """模拟多条假设业绩下的奖金结果。

    Args:
        body: 模拟请求（规则 ID + 假设场景列表）。
        _: 当前登录用户（manager 权限）。
        service: 激励规则服务。

    Returns:
        每个场景的试算结果列表。
    """
    results = service.simulate(rule_id=body.rule_id, hypotheticals=body.hypotheticals)
    return success(data=results)


@router.post("/approve")
def approve(
    body: ApproveRequest,
    _: dict = Depends(require_scope("manager")),
    service: IncentiveService = Depends(),
) -> Any:
    """审批通过一条激励规则。

    Args:
        body: 审批请求（规则 ID + 审批人）。
        _: 当前登录用户（manager 权限）。
        service: 激励规则服务。

    Returns:
        更新后的规则信息。
    """
    rule = service.approve(rule_id=body.rule_id, approver=body.approver)
    return success(data=rule)


@router.get("/rules/{rule_id:int}")
def get_detail(
    rule_id: int,
    _: dict = Depends(require_scope("manager")),
    service: IncentiveService = Depends(),
) -> Any:
    """查询单条激励规则的完整信息。

    Args:
        rule_id: 规则 ID。
        _: 当前登录用户（manager 权限）。
        service: 激励规则服务。

    Returns:
        规则详情。
    """
    rule = service.get_detail(rule_id=rule_id)
    return success(data=rule)
