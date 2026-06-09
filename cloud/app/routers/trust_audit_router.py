"""信任审计路由：信任评分计算、审计区块创建与链验证。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from cloud.app.services.trust_audit_service import TrustAuditService
from shared.auth import get_current_user

router = APIRouter(prefix="/api/trust-audit", tags=["信任审计"])


class CreateBlockRequest(BaseModel):
    """CreateBlockRequest 服务类。"""

    data: dict = {}
    block_type: str = "audit"
    node_id: str = ""
    created_by: str = ""


@router.get("/score/{node_id}", summary="Get Trust Score by ID", description="根据节点ID计算信任评分", tags=["信任审计"])
def get_trust_score(
    node_id: str,
    current_user: dict = Depends(get_current_user),
    service: TrustAuditService = Depends(),
):
    """get_trust_score 操作。

    Args:
        node_id: 描述
        current_user: 描述
        service: 描述
    """
    result = service.calculate_trust_score(node_id)
    return {"code": 0, "data": result, "message": "success"}


@router.post("/blocks", status_code=201, summary="Create Block", description="创建新的审计区块", tags=["信任审计"])
def create_block(
    body: CreateBlockRequest,
    current_user: dict = Depends(get_current_user),
    service: TrustAuditService = Depends(),
):
    """create_block 操作。

    Args:
        current_user: 描述
        service: 描述
    """
    result = service.create_audit_block(
        data=body.data,
        block_type=body.block_type,
        node_id=body.node_id,
        created_by=body.created_by,
    )
    return {"code": 0, "data": result, "message": "success"}


@router.get("/verify", summary="Verify Chain", description="验证信任审计链的完整性", tags=["信任审计"])
def verify_chain(
    current_user: dict = Depends(get_current_user),
    service: TrustAuditService = Depends(),
):
    """verify_chain 操作。

    Args:
        current_user: 描述
        service: 描述
    """
    result = service.verify_chain()
    return {"code": 0, "data": result, "message": "success"}


@router.get("/blocks", summary="List all Blocks", description="分页查询审计区块列表，可按节点ID过滤", tags=["信任审计"])
def list_blocks(
    node_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    service: TrustAuditService = Depends(),
):
    """list_blocks 操作。

    Args:
        node_id: 描述
        limit: 描述
        current_user: 描述
        service: 描述
    """
    result = service.get_chain(node_id=node_id or "", limit=limit)
    return {"code": 0, "data": result, "message": "success"}
