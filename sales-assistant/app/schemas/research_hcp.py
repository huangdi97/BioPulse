"""Research HCP extended profile schemas."""

from pydantic import BaseModel, Field


class PaperInfo(BaseModel):
    id: str
    title: str
    journal: str
    year: int
    citations: int = Field(default=0, ge=0)
    impact_factor: float = Field(default=0, ge=0)


class GrantInfo(BaseModel):
    id: str
    title: str
    source: str
    amount: float = Field(default=0, ge=0)
    year: int
    status: str = "active"


class ExperimentMethod(BaseModel):
    id: str
    name: str
    category: str
    description: str = ""


class ResearchProfile(BaseModel):
    papers: list[PaperInfo] = Field(default_factory=list)
    grants: list[GrantInfo] = Field(default_factory=list)
    experiments: list[ExperimentMethod] = Field(default_factory=list)
    h_index: int = Field(default=0, ge=0)
    impact_factor: float = Field(default=0, ge=0)
    score: float = Field(default=0, ge=0, le=100)
