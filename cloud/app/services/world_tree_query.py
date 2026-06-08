"""世界树查询方法。"""

import json
from typing import Dict, List, Optional


class WorldTreeQueryMixin:
    """世界树节点查询与记忆查询方法。"""

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
