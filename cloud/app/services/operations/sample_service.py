"""样品管理服务，管理样品库存、分发、接收确认与合规报告。"""

from datetime import datetime, timezone
from typing import Optional


class SampleService:
    _inventory: dict[int, dict] = {}
    _dispenses: dict[int, dict] = {}
    _next_inv_id: int = 1
    _next_disp_id: int = 1

    def add_inventory(
        self,
        sku: str,
        name: str,
        quantity: int,
        location: str,
        batch: Optional[str] = None,
        expiry: Optional[str] = None,
    ) -> dict:
        inv_id = self._next_inv_id
        self._next_inv_id += 1
        record = {
            "id": inv_id,
            "sku": sku,
            "name": name,
            "quantity": quantity,
            "location": location,
            "batch": batch or "",
            "expiry": expiry or "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._inventory[inv_id] = record
        return dict(record)

    def record_dispense(
        self,
        sample_id: int,
        recipient: str,
        quantity: int,
        purpose: Optional[str] = None,
    ) -> dict:
        item = self._inventory.get(sample_id)
        if not item:
            raise ValueError(f"Sample {sample_id} not found")
        if item["quantity"] < quantity:
            raise ValueError(f"Insufficient quantity for sample {sample_id}")
        item["quantity"] -= quantity

        disp_id = self._next_disp_id
        self._next_disp_id += 1
        record = {
            "id": disp_id,
            "sample_id": sample_id,
            "recipient": recipient,
            "quantity": quantity,
            "purpose": purpose or "",
            "status": "dispensed",
            "dispensed_at": datetime.now(timezone.utc).isoformat(),
        }
        self._dispenses[disp_id] = record
        return dict(record)

    def confirm_receipt(self, sample_id: int, recipient: str) -> dict:
        dispense = self._dispenses.get(sample_id)
        if not dispense:
            raise ValueError(f"Dispense record {sample_id} not found")
        if dispense["recipient"] != recipient:
            raise ValueError(f"Recipient mismatch for dispense {sample_id}")
        if dispense["status"] != "dispensed":
            raise ValueError(f"Dispense {sample_id} already confirmed")
        dispense["status"] = "confirmed"
        dispense["confirmed_at"] = datetime.now(timezone.utc).isoformat()
        return dict(dispense)

    def get_inventory(self, sku: Optional[str] = None) -> list[dict]:
        if sku:
            return [dict(v) for v in self._inventory.values() if v["sku"] == sku]
        return [dict(v) for v in self._inventory.values()]

    def get_alerts(self) -> list[dict]:
        alerts = []
        for item in self._inventory.values():
            if item["quantity"] <= 0:
                alerts.append(
                    {
                        "type": "out_of_stock",
                        "sample_id": item["id"],
                        "sku": item["sku"],
                        "name": item["name"],
                        "message": f"{item['name']} is out of stock",
                    }
                )
            elif item["quantity"] < 10:
                alerts.append(
                    {
                        "type": "low_stock",
                        "sample_id": item["id"],
                        "sku": item["sku"],
                        "name": item["name"],
                        "quantity": item["quantity"],
                        "message": f"{item['name']} is low on stock ({item['quantity']} remaining)",
                    }
                )
            if item["expiry"]:
                expiry_date = item["expiry"]
                if expiry_date <= datetime.now(timezone.utc).strftime("%Y-%m-%d"):
                    alerts.append(
                        {
                            "type": "expired",
                            "sample_id": item["id"],
                            "sku": item["sku"],
                            "name": item["name"],
                            "message": f"{item['name']} has expired ({expiry_date})",
                        }
                    )
        return alerts

    def get_compliance_report(self) -> dict:
        total_dispensed = sum(d["quantity"] for d in self._dispenses.values())
        confirmed = sum(1 for d in self._dispenses.values() if d["status"] == "confirmed")
        pending = sum(1 for d in self._dispenses.values() if d["status"] == "dispensed")
        return {
            "total_inventory_items": len(self._inventory),
            "total_dispensed_quantity": total_dispensed,
            "total_dispense_records": len(self._dispenses),
            "confirmed_receipts": confirmed,
            "pending_confirmation": pending,
            "alerts": self.get_alerts(),
        }
