import json
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import HTTPException

from cloud.app.repositories import (
    MemoryEntriesRepository,
    NodeMemoryLinksRepository,
    WorldTreeNodesRepository,
    WorldTreeSnapshotsRepository,
)
from cloud.app.services.base import BaseService


class WorldTreeService(BaseService):
    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _n404(self, name: str = "Node") -> HTTPException:
        return HTTPException(status_code=404, detail=f"{name} not found")

    def _get_repos(self):
        return (
            WorldTreeNodesRepository(self.db),
            WorldTreeSnapshotsRepository(self.db),
            NodeMemoryLinksRepository(self.db),
            MemoryEntriesRepository(self.db),
        )

    def _node_or_404(self, nodes_repo: WorldTreeNodesRepository, node_id: int) -> dict:
        row = nodes_repo.get_by_id(node_id)
        if not row:
            raise self._n404()
        return row

    def _build(self, row) -> dict:
        d = dict(row) if not isinstance(row, dict) else row
        d["metadata"] = json.loads(d.get("metadata") or "{}")
        return d

    def _refresh_path(self, node_id: int) -> None:
        nodes_repo = WorldTreeNodesRepository(self.db)
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
        nodes_repo.update_path(node_id, path, level, self._now())

    def _refresh_children(self, parent_id: int) -> None:
        nodes_repo = WorldTreeNodesRepository(self.db)
        children = nodes_repo.list_all(conditions=["parent_id=?"], params=[parent_id], order_by="id ASC")
        for child in children:
            self._refresh_path(child["id"])
            self._refresh_children(child["id"])

    def create_node(
        self,
        name: str,
        description: str,
        parent_id: Optional[int],
        node_type: str,
        sort_order: int,
        metadata: dict,
        uid: int,
    ) -> dict:
        now = self._now()
        nodes_repo, _, _, _ = self._get_repos()

        if parent_id is None:
            path, level = "/" + name, 0
        else:
            p = nodes_repo.get_by_id(parent_id)
            if not p:
                raise self._n404("Parent")
            path, level = p["path"] + "/" + name, p["level"] + 1

        node_id = nodes_repo.create(
            {
                "name": name,
                "description": description,
                "parent_id": parent_id,
                "path": path,
                "level": level,
                "node_type": node_type,
                "sort_order": sort_order,
                "metadata": json.dumps(metadata, ensure_ascii=False),
                "created_by": uid,
                "created_at": now,
                "updated_at": now,
            }
        )
        return self._build(nodes_repo.get_by_id(node_id))

    def list_nodes(self, node_type: Optional[str] = None, parent_id: Optional[int] = None) -> List[dict]:
        nodes_repo, _, _, _ = self._get_repos()
        conditions, params = [], []
        if node_type:
            conditions.append("node_type=?")
            params.append(node_type)
        if parent_id is not None:
            conditions.append("parent_id=?")
            params.append(parent_id)
        elif not node_type:
            conditions.append("parent_id IS NULL")
        rows = nodes_repo.list_all(
            conditions=conditions or None,
            params=params or None,
            order_by="sort_order, name",
        )
        return [self._build(r) for r in rows]

    def get_node(self, node_id: int) -> dict:
        nodes_repo, _, nml_repo, _ = self._get_repos()
        n = self._node_or_404(nodes_repo, node_id)
        d = self._build(n)
        d["child_count"] = nodes_repo.count(conditions=["parent_id=?"], params=[node_id])
        d["memory_count"] = nml_repo.count_by_node(node_id)
        return d

    def update_node(
        self,
        node_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        node_type: Optional[str] = None,
        sort_order: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        nodes_repo, _, _, _ = self._get_repos()
        n = self._node_or_404(nodes_repo, node_id)
        old_pid = n["parent_id"]
        now = self._now()
        renamed = False

        updates = {}
        if name is not None:
            updates["name"] = name
            renamed = True
        if description is not None:
            updates["description"] = description
        if node_type is not None:
            updates["node_type"] = node_type
        if sort_order is not None:
            updates["sort_order"] = sort_order
        if metadata is not None:
            updates["metadata"] = json.dumps(metadata, ensure_ascii=False)

        if updates:
            nodes_repo.update(node_id, updates)
        nodes_repo.update_path(node_id, n.get("path", ""), n.get("level", 0), now)

        if renamed or old_pid != n["parent_id"]:
            self._refresh_path(node_id)
            self._refresh_children(node_id)
        return self._build(nodes_repo.get_by_id(node_id))

    def delete_node(self, node_id: int) -> str:
        nodes_repo, snapshots_repo, nml_repo, _ = self._get_repos()
        self._node_or_404(nodes_repo, node_id)
        ids = nodes_repo.descendant_ids(node_id)
        nml_repo.delete_by_nodes(ids)
        snapshots_repo.delete_by_nodes(ids)
        for nid in reversed(ids):
            nodes_repo.delete(nid)
        return f"Deleted node {node_id} and {len(ids) - 1} descendants"

    def get_children(self, node_id: int) -> List[dict]:
        nodes_repo, _, _, _ = self._get_repos()
        self._node_or_404(nodes_repo, node_id)
        rows = nodes_repo.list_all(conditions=["parent_id=?"], params=[node_id], order_by="sort_order, name")
        return [self._build(r) for r in rows]

    def get_ancestors(self, node_id: int) -> List[dict]:
        nodes_repo, _, _, _ = self._get_repos()
        ancestors = []
        cur = self._node_or_404(nodes_repo, node_id)
        while cur["parent_id"] is not None:
            parent = nodes_repo.get_by_id(cur["parent_id"])
            if not parent:
                break
            ancestors.append(self._build(parent))
            cur = parent
        return ancestors

    def link_memory(self, node_id: int, memory_id: int) -> None:
        nodes_repo, _, nml_repo, mem_repo = self._get_repos()
        self._node_or_404(nodes_repo, node_id)
        if not mem_repo.find_active_by_id(memory_id):
            raise self._n404("Memory entry")
        nml_repo.create(
            {
                "node_id": node_id,
                "memory_entry_id": memory_id,
                "created_at": self._now(),
            }
        )

    def unlink_memory(self, node_id: int, memory_id: int) -> None:
        nodes_repo, _, _, _ = self._get_repos()
        self._node_or_404(nodes_repo, node_id)
        self.db.execute(
            "DELETE FROM node_memory_links WHERE node_id=? AND memory_entry_id=?",
            (node_id, memory_id),
        )
        self.db.commit()

    def get_node_memories(self, node_id: int) -> List[dict]:
        nodes_repo, _, _, _ = self._get_repos()
        self._node_or_404(nodes_repo, node_id)
        rows = self.db.execute(
            "SELECT me.*, nml.relevance_score FROM memory_entries me "
            "JOIN node_memory_links nml ON me.id=nml.memory_entry_id "
            "WHERE nml.node_id=? AND me.is_active=1 "
            "ORDER BY nml.relevance_score DESC, me.importance DESC",
            (node_id,),
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["context_tags"] = json.loads(d.get("context_tags") or "[]")
            results.append(d)
        return results

    def get_full_tree(self) -> List[dict]:
        nodes_repo, _, nml_repo, _ = self._get_repos()
        rows = nodes_repo.list_active_sorted()
        nodes = [self._build(r) for r in rows]
        node_map: Dict[int, dict] = {n["id"]: n for n in nodes}
        for n in nodes:
            n["children"] = []
            n["memory_count"] = nml_repo.count_by_node(n["id"])
        roots = []
        for n in nodes:
            if n["parent_id"] is None:
                roots.append(n)
            elif n["parent_id"] in node_map:
                node_map[n["parent_id"]]["children"].append(n)
        return roots
