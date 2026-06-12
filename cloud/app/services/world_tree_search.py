"""World tree search, path management, and data conversion utilities."""

import json

from fastapi import HTTPException

from cloud.app.repositories import WorldTreeNodesRepository
from shared.datetime_utils import now as _now


def _n404(name: str = "Node") -> HTTPException:
    return HTTPException(status_code=404, detail=f"{name} not found")


def _get_repos(db):
    from cloud.app.repositories import (
        MemoryEntriesRepository,
        NodeMemoryLinksRepository,
        WorldTreeNodesRepository,
        WorldTreeSnapshotsRepository,
    )

    return (
        WorldTreeNodesRepository(db),
        WorldTreeSnapshotsRepository(db),
        NodeMemoryLinksRepository(db),
        MemoryEntriesRepository(db),
    )


def _node_or_404(db, node_id: int) -> dict:
    nodes_repo = WorldTreeNodesRepository(db)
    row = nodes_repo.get_by_id(node_id)
    if not row:
        raise _n404()
    return row


def _build(row) -> dict:
    d = dict(row) if not isinstance(row, dict) else row
    d["metadata"] = json.loads(d.get("metadata") or "{}")
    return d


def _refresh_path(db, node_id: int) -> None:
    nodes_repo = WorldTreeNodesRepository(db)
    node = nodes_repo.get_by_id(node_id)
    if not node:
        return
    if node["parent_id"] is None:
        path, level = "/" + node["name"], 0
    else:
        parent = nodes_repo.get_by_id(node["parent_id"])
        if not parent:
            return
        path, level = parent["path"] + "/" + node["name"], parent["level"] + 1
    nodes_repo.update_path(node_id, path, level, _now())


def _refresh_children(db, parent_id: int) -> None:
    nodes_repo = WorldTreeNodesRepository(db)
    children = nodes_repo.list_all(conditions=["parent_id=?"], params=[parent_id], order_by="id ASC")
    for child in children:
        _refresh_path(db, child["id"])
        _refresh_children(db, child["id"])
