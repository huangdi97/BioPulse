"""Inventory warning schemas."""

from pydantic import BaseModel, Field


class InventoryItem(BaseModel):
    product_id: str
    name: str
    current_stock: int = Field(..., ge=0)
    safety_stock: int = Field(..., ge=0)
    unit: str
    location: str


class InventoryAlert(BaseModel):
    item_id: str
    alert_type: str
    message: str
    severity: str


class WarningConfig(BaseModel):
    safety_stock_threshold: int = Field(..., ge=0)
    auto_notify: bool = True
