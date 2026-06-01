from cloud.shared.repository import BaseRepository
from cloud.shared.columns import (
    TABLE_MEMORY_ENTRIES_COLS,
    TABLE_MEMORY_GATES_COLS,
    TABLE_MEMORY_RECALL_LOG_COLS,
    TABLE_MEMORY_CONSOLIDATION_LOG_COLS,
    TABLE_MEMORY_UTILITY_SCORES_COLS,
    TABLE_EPISODIC_MEMORY_COLS,
    TABLE_WORKING_MEMORY_COLS,
    TABLE_NODE_MEMORY_LINKS_COLS,
    TABLE_SLEEP_CONSOLIDATION_LOGS_COLS,
)


class MemoryEntriesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "memory_entries", TABLE_MEMORY_ENTRIES_COLS)

    def list_active_ordered(self, order_by="importance DESC"):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} "
            f"WHERE is_active=1 ORDER BY {order_by}"
        ).fetchall()
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
            f"SELECT {placeholders} FROM {self.table_name} "
            "WHERE source_type=? AND source_id=? AND is_active=1",
            (source_type, source_id),
        ).fetchone()
        return dict(row) if row else None

    def list_filtered(
        self, memory_type=None, importance_min=None, keyword=None, page=1, page_size=20
    ):
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
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE is_active=1"
        ).fetchone()[0]

    def by_type_stats(self):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT memory_type, COUNT(*) AS cnt, AVG(importance) AS avg_imp "
            f"FROM {self.table_name} WHERE is_active=1 GROUP BY memory_type"
        ).fetchall()
        return [dict(r) for r in rows]

    def all_context_tags_active(self):
        rows = self.db.execute(
            f"SELECT context_tags FROM {self.table_name} WHERE is_active=1"
        ).fetchall()
        return [dict(r) for r in rows]

    def increment_access(self, entry_id, now):
        self.db.execute(
            "UPDATE memory_entries SET access_count = access_count + 1, "
            "last_accessed = ? WHERE id = ?",
            (now, entry_id),
        )

    def find_similar_by_title(self, prefix, exclude_id, min_utility=0.8):
        placeholders = ", ".join(self.cols)
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


class MemoryGatesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "memory_gates", TABLE_MEMORY_GATES_COLS)

    def list_ordered(self):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]

    def find_active_by_source_type(self, source_type):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} "
            "WHERE source_type=? AND is_active=1",
            (source_type,),
        ).fetchone()
        return dict(row) if row else None


class MemoryRecallLogRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "memory_recall_log", TABLE_MEMORY_RECALL_LOG_COLS)

    def list_recent(self, limit=5):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


class MemoryConsolidationLogRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(
            db, "memory_consolidation_log", TABLE_MEMORY_CONSOLIDATION_LOG_COLS
        )

    def list_recent(self, limit=5):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def count_by_type_since(self, consolidation_type, since):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} "
            "WHERE consolidation_type=? AND created_at >= ?",
            (consolidation_type, since),
        ).fetchone()[0]

    def trend_since(self, since):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT date(created_at) as day, consolidation_type, COUNT(*) as cnt "
            f"FROM {self.table_name} WHERE created_at >= ? "
            "GROUP BY date(created_at), consolidation_type ORDER BY day ASC",
            (since,),
        ).fetchall()
        return [dict(r) for r in rows]


class MemoryUtilityScoresRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "memory_utility_scores", TABLE_MEMORY_UTILITY_SCORES_COLS)

    def upsert_score(self, data):
        filtered = {k: v for k, v in data.items() if k in self.cols}
        if not filtered:
            return
        cols_str = ", ".join(filtered.keys())
        placeholders = ", ".join(["?"] * len(filtered))
        self.db.execute(
            f"INSERT OR REPLACE INTO {self.table_name} ({cols_str}) VALUES ({placeholders})",
            list(filtered.values()),
        )

    def list_ranked(self, min_utility=0.0, limit=20):
        rows = self.db.execute(
            "SELECT me.id, me.title, me.memory_type, me.importance, me.access_count, "
            "me.last_accessed, mus.utility_score, mus.recency_score, mus.connectivity_score "
            "FROM memory_entries me JOIN memory_utility_scores mus ON me.id=mus.memory_entry_id "
            "WHERE mus.utility_score >= ? AND me.is_active=1 "
            "ORDER BY mus.utility_score DESC LIMIT ?",
            (min_utility, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def find_by_memory(self, memory_entry_id):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE memory_entry_id=?",
            (memory_entry_id,),
        ).fetchone()
        return dict(row) if row else None


class EpisodicMemoryRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "episodic_memory", TABLE_EPISODIC_MEMORY_COLS)

    def find_unconsolidated(self):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} "
            "WHERE is_consolidated=0 OR is_consolidated IS NULL"
        ).fetchall()
        return [dict(r) for r in rows]

    def count_by_creator(self, creator_id):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE created_by=?",
            (creator_id,),
        ).fetchone()[0]


class WorkingMemoryRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "working_memory", TABLE_WORKING_MEMORY_COLS)


class NodeMemoryLinksRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "node_memory_links", TABLE_NODE_MEMORY_LINKS_COLS)

    def count_by_node(self, node_id):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE node_id=?", (node_id,)
        ).fetchone()[0]

    def delete_by_node(self, node_id):
        self.db.execute(f"DELETE FROM {self.table_name} WHERE node_id=?", (node_id,))

    def delete_by_nodes(self, node_ids):
        if not node_ids:
            return
        ph = ",".join("?" for _ in node_ids)
        self.db.execute(
            f"DELETE FROM {self.table_name} WHERE node_id IN ({ph})", node_ids
        )

    def memory_ids_for_nodes(self, node_ids):
        if not node_ids:
            return []
        ph = ",".join("?" for _ in node_ids)
        rows = self.db.execute(
            f"SELECT DISTINCT me.id, me.title FROM memory_entries me "
            f"JOIN {self.table_name} nml ON me.id=nml.memory_entry_id "
            f"WHERE nml.node_id IN ({ph}) AND me.is_active=1",
            node_ids,
        ).fetchall()
        return [dict(r) for r in rows]

    def importance_for_nodes(self, node_ids):
        if not node_ids:
            return []
        ph = ",".join("?" for _ in node_ids)
        rows = self.db.execute(
            f"SELECT me.importance FROM memory_entries me "
            f"JOIN {self.table_name} nml ON me.id=nml.memory_entry_id "
            f"WHERE nml.node_id IN ({ph})",
            node_ids,
        ).fetchall()
        return [dict(r) for r in rows]

    def memory_entries_with_utility(self):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            "SELECT me.id, me.title, me.content, me.importance, me.access_count, "
            "me.last_accessed, me.is_active, mus.utility_score "
            "FROM memory_entries me "
            "JOIN memory_utility_scores mus ON me.id=mus.memory_entry_id "
            "WHERE me.is_active=1"
        ).fetchall()
        return [dict(r) for r in rows]


class SleepConsolidationLogsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(
            db, "sleep_consolidation_logs", TABLE_SLEEP_CONSOLIDATION_LOGS_COLS
        )

    def list_recent(self, limit=10):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
