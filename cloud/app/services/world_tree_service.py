"""世界树服务管理层级化知识树结构。"""

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
    """世界树服务，管理层次化知识树节点的增删改查与记忆关联。"""

    def _now(self) -> str:
        """返回当前时间字符串。"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _n404(self, name: str = "Node") -> HTTPException:
        """构造 404 异常。

        Args:
            name: 资源名称

        Returns:
            HTTPException 实例
        """
        return HTTPException(status_code=404, detail=f"{name} not found")

    def _get_repos(self):
        """获取世界树相关的四个仓库实例。

        Returns:
            (nodes_repo, snapshots_repo, links_repo, memory_repo) 元组
        """
        return (
            WorldTreeNodesRepository(self.db),
            WorldTreeSnapshotsRepository(self.db),
            NodeMemoryLinksRepository(self.db),
            MemoryEntriesRepository(self.db),
        )

    def _node_or_404(self, nodes_repo: WorldTreeNodesRepository, node_id: int) -> dict:
        """按 ID 获取节点，不存在则抛出 404。

        Args:
            nodes_repo: 节点仓库
            node_id: 节点 ID

        Returns:
            节点记录字典

        Raises:
            HTTPException: 节点不存在时返回 404
        """
        row = nodes_repo.get_by_id(node_id)
        if not row:
            raise self._n404()
        return row

    def _build(self, row) -> dict:
        """将数据库行转为带解析 metadata 的字典。

        Args:
            row: 数据库行或字典

        Returns:
            含解析后 metadata 的节点字典
        """
        d = dict(row) if not isinstance(row, dict) else row
        d["metadata"] = json.loads(d.get("metadata") or "{}")
        return d

    def _refresh_path(self, node_id: int) -> None:
        """刷新单个节点的路径和层级。

        Args:
            node_id: 节点 ID
        """
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
        """递归刷新所有子节点的路径和层级。

        Args:
            parent_id: 父节点 ID
        """
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
        """创建世界树节点。

        Args:
            name: 节点名称
            description: 节点描述
            parent_id: 父节点 ID，None 表示根节点
            node_type: 节点类型
            sort_order: 排序序号
            metadata: 节点元数据字典
            uid: 创建者用户 ID

        Returns:
            新创建的节点记录字典

        Raises:
            HTTPException: 父节点不存在时返回 404
        """
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
        """查询节点列表。

        Args:
            node_type: 可选，按节点类型过滤
            parent_id: 可选，按父节点 ID 过滤；均未指定时返回根节点

        Returns:
            节点记录列表，按排序号和名称排序
        """
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
        """获取单个节点详情，含子节点数和关联记忆数。

        Args:
            node_id: 节点 ID

        Returns:
            节点记录字典，含 child_count 和 memory_count 字段

        Raises:
            HTTPException: 节点不存在时返回 404
        """
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
        """更新节点属性，并刷新自身及后代路径。

        Args:
            node_id: 节点 ID
            name: 可选，新名称（会触发路径刷新）
            description: 可选，新描述
            node_type: 可选，新节点类型
            sort_order: 可选，新排序序号
            metadata: 可选，新元数据字典

        Returns:
            更新后的节点记录字典

        Raises:
            HTTPException: 节点不存在时返回 404
        """
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
        """删除节点及其所有后代节点。

        Args:
            node_id: 根节点 ID

        Returns:
            包含删除结果的描述字符串

        Raises:
            HTTPException: 节点不存在时返回 404
        """
        nodes_repo, snapshots_repo, nml_repo, _ = self._get_repos()
        self._node_or_404(nodes_repo, node_id)
        ids = nodes_repo.descendant_ids(node_id)
        nml_repo.delete_by_nodes(ids)
        snapshots_repo.delete_by_nodes(ids)
        for nid in reversed(ids):
            nodes_repo.delete(nid)
        return f"Deleted node {node_id} and {len(ids) - 1} descendants"

    def get_children(self, node_id: int) -> List[dict]:
        """获取节点的直接子节点列表。

        Args:
            node_id: 节点 ID

        Returns:
            子节点记录列表，按排序号和名称排序

        Raises:
            HTTPException: 节点不存在时返回 404
        """
        nodes_repo, _, _, _ = self._get_repos()
        self._node_or_404(nodes_repo, node_id)
        rows = nodes_repo.list_all(conditions=["parent_id=?"], params=[node_id], order_by="sort_order, name")
        return [self._build(r) for r in rows]

    def get_ancestors(self, node_id: int) -> List[dict]:
        """获取节点从根到父节点的所有祖先节点。

        Args:
            node_id: 节点 ID

        Returns:
            祖先节点记录列表，从直接父节点到根节点

        Raises:
            HTTPException: 节点不存在时返回 404
        """
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
        """将记忆条目关联到节点。

        Args:
            node_id: 节点 ID
            memory_id: 记忆条目 ID

        Raises:
            HTTPException: 节点或记忆条目不存在时返回 404
        """
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
        """取消节点与记忆条目的关联。

        Args:
            node_id: 节点 ID
            memory_id: 记忆条目 ID

        Raises:
            HTTPException: 节点不存在时返回 404
        """
        nodes_repo, _, _, _ = self._get_repos()
        self._node_or_404(nodes_repo, node_id)
        self.db.execute(
            "DELETE FROM node_memory_links WHERE node_id=? AND memory_entry_id=?",
            (node_id, memory_id),
        )
        self.db.commit()

    def get_node_memories(self, node_id: int) -> List[dict]:
        """获取节点关联的所有记忆条目。

        Args:
            node_id: 节点 ID

        Returns:
            记忆条目记录列表，按关联评分和重要性排序

        Raises:
            HTTPException: 节点不存在时返回 404
        """
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
        """获取完整的世界树结构，以嵌套子节点形式返回。

        Returns:
            根节点列表，每个节点含嵌套 children 列表和 memory_count
        """
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
