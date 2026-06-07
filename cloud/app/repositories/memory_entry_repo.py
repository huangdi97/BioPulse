"""记忆条目数据访问层。"""

from cloud.shared.repository import BaseRepository
from shared.columns import TABLE_MEMORY_ENTRIES_COLS


class MemoryEntriesRepository(BaseRepository):
    """记忆条目表。"""

    def __init__(self, db):
        super().__init__(db, "memory_entries", TABLE_MEMORY_ENTRIES_COLS)

    def list_active_ordered(self, order_by="importance DESC"):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(f"SELECT {placeholders} FROM {self.table_name} WHERE is_active=1 ORDER BY {order_by}").fetchall()
        return [dict(r) for r in rows]

    def find_active_by_id(self, entry_id):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE id=? AND is_active=1",
            (entry_id,),
        ).fetchone()
        return dict(row) if row else None

    def find_by_source_active(self, source_type, source_id):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE source_type=? AND source_id=? AND is_active=1",
            (source_type, source_id),
        ).fetchone()
        return dict(row) if row else None

    def list_filtered(self, memory_type=None, importance_min=None, keyword=None, page=1, page_size=20):
        conditions, params = ["is_active = 1"], []
        if memory_type:
            conditions.append("memory_type = ?")
            params.append(memory_type)
        if importance_min is not None:
            conditions.append("importance >= ?")
            params.append(importance_min)
        if keyword:
            conditions.append("(title LIKE ? OR content LIKE ?)")
            kw = f"%{keyword}%"
            params.extend([kw, kw])
        return self.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params,
            order_by="importance DESC",
        )

    def count_active(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE is_active=1").fetchone()[0]

    def by_type_stats(self):
        ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT memory_type, COUNT(*) AS cnt, AVG(importance) AS avg_imp FROM {self.table_name} WHERE is_active=1 GROUP BY memory_type"
        ).fetchall()
        return [dict(r) for r in rows]

    def all_context_tags_active(self):
        rows = self.db.execute(f"SELECT context_tags FROM {self.table_name} WHERE is_active=1").fetchall()
        return [dict(r) for r in rows]

    def increment_access(self, entry_id, now):
        self.db.execute(
            "UPDATE memory_entries SET access_count = access_count + 1, last_accessed = ? WHERE id = ?",
            (now, entry_id),
        )

    def find_similar_by_title(self, prefix, exclude_id, min_utility=0.8):
        ", ".join(self.cols)
        rows = self.db.execute(
            "SELECT me2.id FROM memory_entries me2 "
            "JOIN memory_utility_scores mus2 ON me2.id=mus2.memory_entry_id "
            "WHERE me2.id!=? AND me2.is_active=1 AND me2.title LIKE ? "
            "AND mus2.utility_score >= ?",
            (exclude_id, prefix + "%", min_utility),
        ).fetchall()
        return [dict(r) for r in rows]

    def deactivate(self, entry_id, now):
        self.db.execute(
            "UPDATE memory_entries SET is_active=0, updated_at=? WHERE id=?",
            (now, entry_id),
        )

    def append_content(self, content片段, target_id, now):
        self.db.execute(
            "UPDATE memory_entries SET content=content || ? || ?, updated_at=? WHERE id=?",
            ("\n\n[MERGED] ", content片段, now, target_id),
        )

    def promote_importance(self, new_imp, entry_id, now):
        self.db.execute(
            "UPDATE memory_entries SET importance=?, updated_at=? WHERE id=?",
            (new_imp, now, entry_id),
        )
