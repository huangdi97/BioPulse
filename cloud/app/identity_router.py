"""DID 去中心化身份路由。"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/identity", tags=["DID身份"])


class VcIssueRequest(BaseModel):
    """VcIssueRequest 服务类。"""

    did: str
    claims: dict = {}


@router.post("/did/create", summary="Create Did")
def create_did(_=Depends(require_scope(["admin"]))):
    """create_did 操作。

    Args:
        _: 描述
    """
    return success(data={"did": "did:example:123"})


@router.get("/did/{did}", summary="Resolve Did")
def resolve_did(did: str, _=Depends(require_scope(["admin"]))):
    """resolve_did 操作。

    Args:
        did: 描述
        _: 描述
    """
    return success(data={"did": did, "document": {}})


@router.post("/vc/issue", summary="Issue Vc")
def issue_vc(body: VcIssueRequest, _=Depends(require_scope(["admin"]))):
    """issue_vc 操作。

    Args:
        _: 描述
    """
    return success(data={"vc": {"id": "vc:1", "type": "VerifiableCredential", "issuer": body.did}})
