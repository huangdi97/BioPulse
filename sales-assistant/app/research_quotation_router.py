"""Research quotation router backed by an in-memory store."""

from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from typing import Any

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/api/research/quotation")

_QUOTATIONS: list[dict[str, Any]] = []
_QUOTATION_LOCK = Lock()
_NEXT_ID = 1


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _success(data: Any) -> dict[str, Any]:
    return {"code": 0, "data": data, "message": "success"}


def _find_index(quotation_id: int) -> int:
    for index, quotation in enumerate(_QUOTATIONS):
        if quotation["id"] == quotation_id:
            return index
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found")


@router.get("", tags=["科研PI"])
def list_quotations() -> dict[str, Any]:
    """List all in-memory research quotations."""
    with _QUOTATION_LOCK:
        quotations = [quotation.copy() for quotation in _QUOTATIONS]
    return _success(quotations)


@router.post("", status_code=status.HTTP_201_CREATED, tags=["科研PI"])
def create_quotation(payload: dict[str, Any]) -> dict[str, Any]:
    """Create a research quotation in memory."""
    global _NEXT_ID

    now = _now_iso()
    with _QUOTATION_LOCK:
        quotation = {
            **payload,
            "id": _NEXT_ID,
            "created_at": now,
            "updated_at": now,
        }
        _NEXT_ID += 1
        _QUOTATIONS.append(quotation)
        result = quotation.copy()

    return _success(result)


@router.get("/{id}", tags=["科研PI"])
def get_quotation_detail(id: int) -> dict[str, Any]:
    """Return one research quotation by id."""
    with _QUOTATION_LOCK:
        quotation = _QUOTATIONS[_find_index(id)].copy()
    return _success(quotation)


@router.put("/{id}", tags=["科研PI"])
def update_quotation(id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Update one research quotation by id."""
    with _QUOTATION_LOCK:
        index = _find_index(id)
        existing = _QUOTATIONS[index]
        updated = {
            **existing,
            **payload,
            "id": id,
            "created_at": existing.get("created_at", _now_iso()),
            "updated_at": _now_iso(),
        }
        _QUOTATIONS[index] = updated
        result = updated.copy()
    return _success(result)


@router.delete("/{id}", tags=["科研PI"])
def delete_quotation(id: int) -> dict[str, Any]:
    """Delete one research quotation by id."""
    with _QUOTATION_LOCK:
        quotation = _QUOTATIONS.pop(_find_index(id))
    return _success(quotation)
