"""Data models for competitor intelligence persistence."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class CompetitorProduct(BaseModel):
    id: int | None = None
    name: str
    company: str = ""
    category: str = ""
    target: str = ""
    mechanism: str = ""
    phase: str = ""
    price: float | None = None
    market_share: float | None = None


class PriceRecord(BaseModel):
    product_id: int
    price: float
    province: str = ""
    date: date | str = Field(default_factory=date.today)
    source: str = ""


class PublicOpinion(BaseModel):
    id: int | None = None
    product_id: int
    platform: str
    title: str = ""
    content: str = ""
    sentiment: str = "neutral"
    publish_date: datetime | date | str | None = None
    url: str = ""


class BiddingRecord(BaseModel):
    product_id: int
    province: str = ""
    winning_price: float | None = None
    manufacturer: str = ""
    round: str = ""
    date: date | str = Field(default_factory=date.today)


__all__ = ["BiddingRecord", "CompetitorProduct", "PriceRecord", "PublicOpinion"]
