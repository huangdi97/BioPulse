"""Inventory warning APIs."""

from fastapi import APIRouter

from assistant.app.schemas.inventory_warning import InventoryAlert, InventoryItem, WarningConfig
from assistant.app.services.inventory_warning_service import (
    check_inventory,
    configure_threshold,
    get_alerts,
    get_inventory_status,
    send_alert,
)

router = APIRouter(prefix="/api/inventory", tags=["库存预警"])


@router.get("/status", response_model=list[InventoryItem], tags=["库存预警"])
def status() -> list[InventoryItem]:
    return get_inventory_status()


@router.get("/alerts", response_model=list[InventoryAlert], tags=["库存预警"])
def alerts() -> list[InventoryAlert]:
    return get_alerts()


@router.put("/{product_id}/threshold", response_model=WarningConfig, tags=["库存预警"])
def threshold(product_id: str, threshold: int) -> WarningConfig:
    return configure_threshold(product_id, threshold)


@router.post("/check", tags=["库存预警"])
def check() -> dict[str, int | str]:
    check_inventory()
    return send_alert()
