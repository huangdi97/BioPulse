from cloud.shared.columns import (
    TABLE_WORLD_TREE_NODES_COLS,
    TABLE_WORLD_TREE_SNAPSHOTS_COLS,
)
from cloud.shared.repository import BaseRepository


class WorldTreeNodesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "world_tree_nodes", TABLE_WORLD_TREE_NODES_COLS)

    def exists_by_id(self, node_id):
        return self.db.execute(f"SELECT id FROM {self.table_name} WHERE id=?", (node_id,)).fetchone() is not None

    def list_active_sorted(self):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(f"SELECT {placeholders} FROM {self.table_name} WHERE is_active=1 ORDER BY sort_order, name").fetchall()
        return [dict(r) for r in rows]

    def descendant_ids(self, node_id):
        ids, stack = [], [node_id]
        while stack:
            cur = stack.pop()
            ids.append(cur)
            stack.extend(c["id"] for c in self.db.execute(f"SELECT id FROM {self.table_name} WHERE parent_id=?", (cur,)).fetchall())
        return ids

    def update_parent(self, node_id, parent_id, now):
        self.db.execute(
            f"UPDATE {self.table_name} SET parent_id=?, updated_at=? WHERE id=?",
            (parent_id, now, node_id),
        )

    def update_path(self, node_id, path, level, now):
        self.db.execute(
            f"UPDATE {self.table_name} SET path=?, level=?, updated_at=? WHERE id=?",
            (path, level, now, node_id),
        )

    def list_by_ids(self, node_ids):
        if not node_ids:
            return []
        ph = ",".join("?" for _ in node_ids)
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE id IN ({ph})",
            node_ids,
        ).fetchall()
        return [dict(r) for r in rows]


class WorldTreeSnapshotsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "world_tree_snapshots", TABLE_WORLD_TREE_SNAPSHOTS_COLS)

    def delete_by_node(self, node_id):
        self.db.execute(f"DELETE FROM {self.table_name} WHERE node_id=?", (node_id,))

    def delete_by_nodes(self, node_ids):
        if not node_ids:
            return
        ph = ",".join("?" for _ in node_ids)
        self.db.execute(f"DELETE FROM {self.table_name} WHERE node_id IN ({ph})", node_ids)
