"""HCP master data management schemas."""

from pydantic import BaseModel, Field


class HCPMaster(BaseModel):
    master_id: str
    primary_name: str
    aliases: list[str] = Field(default_factory=list)
    hospital: str
    department: str
    title: str
    specialty: str
    nmpa_id: str | None = None
    phone: str | None = None
    email: str | None = None
    unified_score: float = Field(..., ge=0, le=100)
    dedup_status: str
    source_systems: list[str] = Field(default_factory=list)


class HCPDedupRule(BaseModel):
    rule_name: str
    match_fields: list[str] = Field(default_factory=list)
    threshold: float = Field(..., ge=0, le=1)
    action: str


class MergeSuggestion(BaseModel):
    primary_id: str
    duplicate_ids: list[str] = Field(default_factory=list)
    match_score: float = Field(..., ge=0, le=1)
