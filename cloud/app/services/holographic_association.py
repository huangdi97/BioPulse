"""全息记忆自动关联逻辑：基于标签、来源和时间维度的关联创建。"""

import json
import logging

from fastapi import HTTPException
from starlette import status

logger = logging.getLogger(__name__)


def _n404(name: str = "Resource") -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{name} not found")


def associate_by_tags(db, entry_id: int, entry: dict, create_association) -> list:
    tags_raw = entry.get("context_tags", "[]")
    if isinstance(tags_raw, str):
        try:
            tags = json.loads(tags_raw)
        except (json.JSONDecodeError, TypeError):
            return []
    elif isinstance(tags_raw, list):
        tags = tags_raw
    else:
        return []
    if not tags:
        return []
    results = []
    for tag in tags:
        rows = db.execute(
            "SELECT id FROM memory_entries WHERE id != ? AND is_active = 1 AND context_tags LIKE ?",
            (entry_id, f"%{tag}%"),
        ).fetchall()
        for row in rows:
            r = create_association(entry_id, row["id"], "shared_tag", 0.8)
            results.append(r)
    return results


def associate_by_source(db, entry_id: int, entry: dict, create_association) -> list:
    source_id = entry.get("source_id", "")
    if not source_id:
        return []
    rows = db.execute(
        "SELECT id FROM memory_entries WHERE id != ? AND is_active = 1 AND source_id = ?",
        (entry_id, source_id),
    ).fetchall()
    results = []
    for row in rows:
        r = create_association(entry_id, row["id"], "same_source", 0.6)
        results.append(r)
    return results


def associate_by_temporal(db, entry_id: int, entry: dict, create_association) -> list:
    memory_type = entry.get("memory_type", "")
    if not memory_type:
        return []
    rows = db.execute(
        "SELECT id FROM memory_entries WHERE id != ? AND is_active = 1 AND memory_type = ? AND date(created_at) = date(?) LIMIT 20",
        (entry_id, memory_type, entry.get("created_at")),
    ).fetchall()
    results = []
    for row in rows:
        r = create_association(entry_id, row["id"], "temporal", 0.5)
        results.append(r)
    return results
