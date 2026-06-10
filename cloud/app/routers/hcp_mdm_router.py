"""HCP master data management APIs."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from cloud.app.services.hcp_mdm_service import dedup_check, get_unified_profile, merge_duplicates
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/api/mdm", tags=["HCP主数据"])


class MergeRequest(BaseModel):
    primary_id: str
    duplicate_ids: list[str] = Field(default_factory=list)


@router.get("/hcp/{id}", tags=["HCP主数据"])
def get_hcp(id: str, _: dict = Depends(require_scope(["pharma", "research"]))):
    return success(data=get_unified_profile(id))


@router.post("/dedup", tags=["HCP主数据"])
def dedup(_: dict = Depends(require_scope(["pharma", "research"]))):
    return success(data=dedup_check())


@router.post("/merge", tags=["HCP主数据"])
def merge(body: MergeRequest, _: dict = Depends(require_scope(["pharma", "research"]))):
    return success(data=merge_duplicates(body.primary_id, body.duplicate_ids))


@router.get("/duplicates", tags=["HCP主数据"])
def duplicates(_: dict = Depends(require_scope(["pharma", "research"]))):
    return success(data=dedup_check())
