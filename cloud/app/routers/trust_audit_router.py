"""信任审计路由：信任评分计算、审计区块创建与链验证。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from cloud.app.services.trust_audit_service import TrustAuditService
from shared.auth_scope import require_scope
from shared.base import success

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
    _: dict = Depends(require_scope("visit")),
    service: TrustAuditService = Depends(),
):
    result = service.calculate_trust_score(node_id)
    return success(data=result)


@router.post("/blocks", status_code=201, summary="Create Block", description="创建新的审计区块", tags=["信任审计"])
def create_block(
    body: CreateBlockRequest,
    _: dict = Depends(require_scope("visit")),
    service: TrustAuditService = Depends(),
):
    result = service.create_audit_block(
        data=body.data,
        block_type=body.block_type,
        node_id=body.node_id,
        created_by=body.created_by,
    )
    return success(data=result)


@router.get("/verify", summary="Verify Chain", description="验证信任审计链的完整性", tags=["信任审计"])
def verify_chain(
    _: dict = Depends(require_scope("visit")),
    service: TrustAuditService = Depends(),
):
    result = service.verify_chain()
    return success(data=result)


@router.get("/blocks", summary="List all Blocks", description="分页查询审计区块列表，可按节点ID过滤", tags=["信任审计"])
def list_blocks(
    node_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    _: dict = Depends(require_scope("visit")),
    service: TrustAuditService = Depends(),
):
    result = service.get_chain(node_id=node_id or "", limit=limit)
    return success(data=result)
