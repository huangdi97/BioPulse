"""Research order router backed by an in-memory store."""

from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from shared.auth_scope import require_scope

router = APIRouter(prefix="/api/research/order")

_ORDERS: list[dict[str, Any]] = []
_ORDER_LOCK = Lock()
_NEXT_ID = 1


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _success(data: Any) -> dict[str, Any]:
    return {"code": 0, "data": data, "message": "success"}


def _find_index(order_id: int) -> int:
    for index, order in enumerate(_ORDERS):
        if order["id"] == order_id:
            return index
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")


@router.get("", tags=["科研PI"])
def list_orders() -> dict[str, Any]:
    """List all in-memory research orders."""
    with _ORDER_LOCK:
        orders = [order.copy() for order in _ORDERS]
    return _success(orders)


@router.post("", status_code=status.HTTP_201_CREATED, tags=["科研PI"])
def create_order(payload: dict[str, Any], _: dict = Depends(require_scope("research"))) -> dict[str, Any]:
    """Create a research order in memory."""
    global _NEXT_ID

    now = _now_iso()
    with _ORDER_LOCK:
        order = {
            **payload,
            "id": _NEXT_ID,
            "status": payload.get("status", "pending"),
            "created_at": now,
            "updated_at": now,
        }
        _NEXT_ID += 1
        _ORDERS.append(order)
        result = order.copy()

    return _success(result)


@router.get("/{id}", tags=["科研PI"])
def get_order_detail(id: int) -> dict[str, Any]:
    """Return one research order by id."""
    with _ORDER_LOCK:
        order = _ORDERS[_find_index(id)].copy()
    return _success(order)


@router.put("/{id}", tags=["科研PI"])
def update_order_status(id: int, payload: dict[str, Any], _: dict = Depends(require_scope("research"))) -> dict[str, Any]:
    """Update one research order status by id."""
    if "status" not in payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="status is required")

    with _ORDER_LOCK:
        index = _find_index(id)
        _ORDERS[index]["status"] = payload["status"]
        _ORDERS[index]["updated_at"] = _now_iso()
        result = _ORDERS[index].copy()

    return _success(result)
