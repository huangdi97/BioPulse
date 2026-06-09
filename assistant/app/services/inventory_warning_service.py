"""Inventory warning service."""

from threading import Lock

from assistant.app.schemas.inventory_warning import InventoryAlert, InventoryItem, WarningConfig

_LOCK = Lock()

_INVENTORY: dict[str, InventoryItem] = {
    "prod-001": InventoryItem(
        product_id="prod-001",
        name="一次性介入导管",
        current_stock=18,
        safety_stock=20,
        unit="支",
        location="上海一院手术库",
    ),
    "prod-002": InventoryItem(
        product_id="prod-002",
        name="球囊扩张套件",
        current_stock=36,
        safety_stock=25,
        unit="套",
        location="上海二院耗材柜",
    ),
    "prod-003": InventoryItem(
        product_id="prod-003",
        name="术中连接线",
        current_stock=4,
        safety_stock=10,
        unit="根",
        location="移动跟台箱",
    ),
}

_CONFIGS: dict[str, WarningConfig] = {
    product_id: WarningConfig(safety_stock_threshold=item.safety_stock, auto_notify=True) for product_id, item in _INVENTORY.items()
}

_LAST_ALERTS: list[InventoryAlert] = []


def _severity(item: InventoryItem) -> str:
    if item.current_stock <= item.safety_stock * 0.5:
        return "critical"
    if item.current_stock < item.safety_stock:
        return "warning"
    return "normal"


def _build_alert(item: InventoryItem) -> InventoryAlert | None:
    severity = _severity(item)
    if severity == "normal":
        return None
    gap = item.safety_stock - item.current_stock
    return InventoryAlert(
        item_id=item.product_id,
        alert_type="low_stock",
        message=f"{item.name}低于安全库存，需补货{gap}{item.unit}以上（{item.location}）",
        severity=severity,
    )


def check_inventory() -> list[InventoryAlert]:
    """Check stock against safety thresholds and return active alerts."""
    with _LOCK:
        alerts = [alert for item in _INVENTORY.values() if (alert := _build_alert(item))]
        _LAST_ALERTS.clear()
        _LAST_ALERTS.extend(alerts)
        return list(_LAST_ALERTS)


def get_inventory_status() -> list[InventoryItem]:
    return list(_INVENTORY.values())


def get_alerts() -> list[InventoryAlert]:
    return check_inventory()


def configure_threshold(product_id: str, threshold: int) -> WarningConfig:
    """Update safety stock threshold for a product."""
    with _LOCK:
        item = _INVENTORY.get(product_id)
        if item is None:
            item = InventoryItem(
                product_id=product_id,
                name=f"未命名产品{product_id}",
                current_stock=0,
                safety_stock=threshold,
                unit="件",
                location="待分配",
            )
        updated_item = item.model_copy(update={"safety_stock": threshold})
        _INVENTORY[product_id] = updated_item
        config = _CONFIGS.get(product_id, WarningConfig(safety_stock_threshold=threshold, auto_notify=True))
        updated_config = config.model_copy(update={"safety_stock_threshold": threshold})
        _CONFIGS[product_id] = updated_config
        return updated_config


def send_alert() -> dict[str, int | str]:
    """Simulate sending current inventory alerts."""
    alerts = check_inventory()
    notified = sum(1 for alert in alerts if _CONFIGS.get(alert.item_id, WarningConfig(safety_stock_threshold=0)).auto_notify)
    return {"status": "sent", "alert_count": len(alerts), "notified_count": notified}
