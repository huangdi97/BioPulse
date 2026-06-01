from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

QUOTATION_TEMPLATES = {
    "reagent": {
        "template_id": "reagent",
        "template_name": "试剂报价模板",
        "description": "适用于生化试剂、检测试剂盒等产品报价",
        "fields": ["name", "catalog_no", "spec", "unit_price", "quantity"],
    },
    "instrument": {
        "template_id": "instrument",
        "template_name": "仪器报价模板",
        "description": "适用于科研仪器、实验设备等产品报价",
        "fields": ["name", "model", "host_price", "accessory_price", "install_fee"],
    },
    "service": {
        "template_id": "service",
        "template_name": "服务报价模板",
        "description": "适用于技术服务、咨询、培训等报价",
        "fields": ["service_name", "unit_price", "person_days", "travel_expense"],
    },
}

TAX_RATE = Decimal("0.13")


def generate_quotation(template_id: str, items: list[dict]) -> dict:
    template = QUOTATION_TEMPLATES.get(template_id)
    if not template:
        raise ValueError(f"Unknown template_id: {template_id}")

    subtotal = Decimal("0.00")

    if template_id == "reagent":
        for item in items:
            qty = Decimal(str(item.get("quantity", 1)))
            price = Decimal(str(item.get("unit_price", 0)))
            item["line_total"] = float(
                (qty * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            )
            subtotal += Decimal(str(item["line_total"]))

    elif template_id == "instrument":
        for item in items:
            host = Decimal(str(item.get("host_price", 0)))
            accessory = Decimal(str(item.get("accessory_price", 0)))
            install = Decimal(str(item.get("install_fee", 0)))
            item["line_total"] = float(
                (host + accessory + install).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            )
            subtotal += Decimal(str(item["line_total"]))

    elif template_id == "service":
        for item in items:
            price = Decimal(str(item.get("unit_price", 0)))
            days = Decimal(str(item.get("person_days", 1)))
            travel = Decimal(str(item.get("travel_expense", 0)))
            item["line_total"] = float(
                (price * days + travel).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            )
            subtotal += Decimal(str(item["line_total"]))

    subtotal = subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    tax = (subtotal * TAX_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total = (subtotal + tax).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "template_id": template_id,
        "template_name": template["template_name"],
        "items": items,
        "subtotal": float(subtotal),
        "tax": float(tax),
        "tax_rate": float(TAX_RATE),
        "total": float(total),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
