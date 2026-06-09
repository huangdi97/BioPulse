"""Competitor quicklook schemas."""

from pydantic import BaseModel, Field


class CompetitorBrief(BaseModel):
    product_id: str = ""
    product_name: str
    company: str
    recent_activity: str
    price_change: str
    key_message: str


class CompetitorActivityBlock(BaseModel):
    title: str = "相关竞品动态"
    hcp_id: str
    window_days: int = 7
    highlights: list[str] = Field(default_factory=list)
    products: list[CompetitorBrief] = Field(default_factory=list)


class QuicklookDashboard(BaseModel):
    hcp_id: str
    window_days: int = 7
    competitors: list[CompetitorBrief] = Field(default_factory=list)
    recent_news: list[str] = Field(default_factory=list)
    change_summary: list[str] = Field(default_factory=list)
    price_trend: list[dict[str, str | float]] = Field(default_factory=list)
    related_competitor_activity: CompetitorActivityBlock
