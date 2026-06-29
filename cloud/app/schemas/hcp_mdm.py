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
    prescription_preference: dict = Field(default_factory=dict)
    academic_influence: float = 0.0
    visit_acceptance: float = 0.0
    channel_preference: list[str] = Field(default_factory=list)


class HCPDedupRule(BaseModel):
    rule_name: str
    match_fields: list[str] = Field(default_factory=list)
    threshold: float = Field(..., ge=0, le=1)
    action: str


class MergeSuggestion(BaseModel):
    primary_id: str
    duplicate_ids: list[str] = Field(default_factory=list)
    match_score: float = Field(..., ge=0, le=1)


class VisitStats(BaseModel):
    total_visits: int = 0
    last_visit_date: str | None = None
    visit_frequency: str = "unknown"
    avg_visit_duration_min: float = 0.0


class HCPProfile(BaseModel):
    master: HCPMaster
    visit_stats: VisitStats


class HCPImportResult(BaseModel):
    imported: int = 0
    skipped: int = 0
    errors: list[str] = Field(default_factory=list)
