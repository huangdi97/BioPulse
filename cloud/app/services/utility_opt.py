"""效用优化服务提供资源配置的优化计算。"""

from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    NodeMemoryLinksRepository,
    WorldTreeNodesRepository,
    WorldTreeSnapshotsRepository,
)


class UtilityOptMixin:
    def subtree_stats(self, node_id: int) -> dict:
        """统计给定节点子树的总节点数、最大深度、记忆数及按层级分布。"""
        tree_repo = WorldTreeNodesRepository(self.db)
        link_repo = NodeMemoryLinksRepository(self.db)

        if not tree_repo.exists_by_id(node_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Node not found")
        desc_ids = tree_repo.descendant_ids(node_id)
        if not desc_ids:
            return {
                "total_nodes": 0,
                "max_depth": 0,
                "total_memories": 0,
                "avg_importance": 0.0,
                "by_level": [],
            }
        levels = tree_repo.list_by_ids(desc_ids)
        max_depth = max(r["level"] for r in levels) if levels else 0
        mem_rows = link_repo.importance_for_nodes(desc_ids)
        total_memories = len(mem_rows)
        avg_importance = round(sum(r["importance"] for r in mem_rows) / total_memories, 4) if total_memories else 0.0
        seen_levels = set()
        by_level = []
        for lr in levels:
            lv = lr["level"]
            if lv not in seen_levels:
                seen_levels.add(lv)
                by_level.append({"level": lv, "count": sum(1 for x in levels if x["level"] == lv)})
        by_level.sort(key=lambda x: x["level"])
        return {
            "total_nodes": len(desc_ids),
            "max_depth": max_depth,
            "total_memories": total_memories,
            "avg_importance": avg_importance,
            "by_level": by_level,
        }

    def move_node(self, node_id: int, new_parent_id: Optional[int]) -> dict:
        """移动节点到新父节点并刷新路径层级。"""
        tree_repo = WorldTreeNodesRepository(self.db)
        node = tree_repo.get_by_id(node_id)
        if not node:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Node not found")
        if new_parent_id is not None:
            if not tree_repo.exists_by_id(new_parent_id):
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Parent node not found")
            desc = tree_repo.descendant_ids(node_id)
            if new_parent_id in desc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot move a node into its own descendant",
                )
        now = self._now()
        tree_repo.update_parent(node_id, new_parent_id, now)
        self._refresh_path(tree_repo, node_id)
        self._refresh_children(tree_repo, node_id)
        self.db.commit()
        return {"message": "Node moved and paths updated"}

    def _refresh_path(self, tree_repo: WorldTreeNodesRepository, node_id: int) -> None:
        node = tree_repo.get_by_id(node_id)
        if not node:
            return
        if node["parent_id"] is None:
            path, level = "/" + node["name"], 0
        else:
            parent = tree_repo.get_by_id(node["parent_id"])
            if not parent:
                return
            path, level = parent["path"] + "/" + node["name"], parent["level"] + 1
        tree_repo.update_path(node_id, path, level, self._now())

    def _refresh_children(self, tree_repo: WorldTreeNodesRepository, parent_id: int) -> None:
        for child in self.db.execute(f"SELECT id FROM {tree_repo.table_name} WHERE parent_id=?", (parent_id,)).fetchall():
            self._refresh_path(tree_repo, child["id"])
            self._refresh_children(tree_repo, child["id"])

    def tree_heatmap(self) -> list[dict]:
        """返回每个世界树节点的名称、层级及关联记忆数量。"""
        tree_repo = WorldTreeNodesRepository(self.db)
        link_repo = NodeMemoryLinksRepository(self.db)

        rows = tree_repo.list_active_sorted()
        result = []
        for r in rows:
            mc = link_repo.count_by_node(r["id"])
            result.append({"name": r["name"], "level": r["level"], "memory_count": mc})
        return result

    def tree_duplicates(self, node_id: int) -> list[dict]:
        """检测子树内标题前缀重复的记忆条目。"""
        tree_repo = WorldTreeNodesRepository(self.db)
        link_repo = NodeMemoryLinksRepository(self.db)

        if not tree_repo.exists_by_id(node_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Node not found")
        desc_ids = tree_repo.descendant_ids(node_id)
        if not desc_ids:
            return []
        mems = link_repo.memory_ids_for_nodes(desc_ids)
        prefix_map = {}
        for m in mems:
            key = m["title"][:20]
            prefix_map.setdefault(key, []).append(dict(m))
        dups = [{"prefix": k, "memories": v} for k, v in prefix_map.items() if len(v) > 1]
        return dups

    def prune_node(self, node_id: int) -> dict:
        """删除非活跃节点及其关联链接和快照。"""
        tree_repo = WorldTreeNodesRepository(self.db)
        link_repo = NodeMemoryLinksRepository(self.db)
        snap_repo = WorldTreeSnapshotsRepository(self.db)

        if not tree_repo.exists_by_id(node_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Node not found")
        desc_ids = tree_repo.descendant_ids(node_id)
        link_repo.delete_by_nodes(desc_ids)
        snap_repo.delete_by_nodes(desc_ids)
        ph = ",".join("?" for _ in desc_ids)
        self.db.execute(f"DELETE FROM world_tree_nodes WHERE id IN ({ph}) AND is_active=0", desc_ids)
        deleted = self.db.total_changes
        self.db.commit()
        return {
            "deleted_count": deleted,
            "message": f"Pruned {deleted} inactive nodes and their links",
        }
