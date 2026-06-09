"""HCP master data management APIs."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from cloud.app.schemas.hcp_mdm import HCPMaster, MergeSuggestion
from cloud.app.services.hcp_mdm_service import dedup_check, get_unified_profile, merge_duplicates

router = APIRouter(prefix="/api/mdm", tags=["HCP主数据"])


class MergeRequest(BaseModel):
    primary_id: str
    duplicate_ids: list[str] = Field(default_factory=list)


@router.get("/hcp/{id}", response_model=HCPMaster, tags=["HCP主数据"])
def get_hcp(id: str) -> HCPMaster:
    return get_unified_profile(id)


@router.post("/dedup", response_model=list[MergeSuggestion], tags=["HCP主数据"])
def dedup() -> list[MergeSuggestion]:
    return dedup_check()


@router.post("/merge", response_model=HCPMaster, tags=["HCP主数据"])
def merge(body: MergeRequest) -> HCPMaster:
    return merge_duplicates(body.primary_id, body.duplicate_ids)


@router.get("/duplicates", response_model=list[MergeSuggestion], tags=["HCP主数据"])
def duplicates() -> list[MergeSuggestion]:
    return dedup_check()
