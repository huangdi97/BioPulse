"""记忆门控、召回日志、巩固日志、效用评分、情景记忆、工作记忆等数据访问层。"""

from cloud.shared.repository import BaseRepository
from shared.columns import (
    TABLE_EPISODIC_MEMORY_COLS,
    TABLE_MEMORY_CONSOLIDATION_LOG_COLS,
    TABLE_MEMORY_GATES_COLS,
    TABLE_MEMORY_RECALL_LOG_COLS,
    TABLE_MEMORY_UTILITY_SCORES_COLS,
    TABLE_NODE_MEMORY_LINKS_COLS,
    TABLE_SLEEP_CONSOLIDATION_LOGS_COLS,
    TABLE_WORKING_MEMORY_COLS,
)


class MemoryGatesRepository(BaseRepository):
    """记忆门控表。"""

    def __init__(self, db):
        super().__init__(db, "memory_gates", TABLE_MEMORY_GATES_COLS)

    def list_ordered(self):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(f"SELECT {placeholders} FROM {self.table_name} ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    def find_active_by_source_type(self, source_type):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE source_type=? AND is_active=1",
            (source_type,),
        ).fetchone()
        return dict(row) if row else None


class MemoryRecallLogRepository(BaseRepository):
    """记忆召回日志表。"""

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
    """记忆巩固日志表。"""

    def __init__(self, db):
        super().__init__(db, "memory_consolidation_log", TABLE_MEMORY_CONSOLIDATION_LOG_COLS)

    def list_recent(self, limit=5):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def count_by_type_since(self, consolidation_type, since):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE consolidation_type=? AND created_at >= ?",
            (consolidation_type, since),
        ).fetchone()[0]

    def trend_since(self, since):
        rows = self.db.execute(
            f"SELECT date(created_at) as day, consolidation_type, COUNT(*) as cnt "
            f"FROM {self.table_name} WHERE created_at >= ? "
            "GROUP BY date(created_at), consolidation_type ORDER BY day ASC",
            (since,),
        ).fetchall()
        return [dict(r) for r in rows]


class MemoryUtilityScoresRepository(BaseRepository):
    """记忆效用评分表。"""

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
    """情景记忆表。"""

    def __init__(self, db):
        super().__init__(db, "episodic_memory", TABLE_EPISODIC_MEMORY_COLS)

    def find_unconsolidated(self):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(f"SELECT {placeholders} FROM {self.table_name} WHERE is_consolidated=0 OR is_consolidated IS NULL").fetchall()
        return [dict(r) for r in rows]

    def count_by_creator(self, creator_id):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE created_by=?",
            (creator_id,),
        ).fetchone()[0]


class WorkingMemoryRepository(BaseRepository):
    """工作记忆表。"""

    def __init__(self, db):
        super().__init__(db, "working_memory", TABLE_WORKING_MEMORY_COLS)


class NodeMemoryLinksRepository(BaseRepository):
    """节点记忆关联表。"""

    def __init__(self, db):
        super().__init__(db, "node_memory_links", TABLE_NODE_MEMORY_LINKS_COLS)

    def count_by_node(self, node_id):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE node_id=?", (node_id,)).fetchone()[0]

    def delete_by_node(self, node_id):
        self.db.execute(f"DELETE FROM {self.table_name} WHERE node_id=?", (node_id,))

    def delete_by_nodes(self, node_ids):
        if not node_ids:
            return
        ph = ",".join("?" for _ in node_ids)
        self.db.execute(f"DELETE FROM {self.table_name} WHERE node_id IN ({ph})", node_ids)

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
            f"SELECT me.importance FROM memory_entries me JOIN {self.table_name} nml ON me.id=nml.memory_entry_id WHERE nml.node_id IN ({ph})",
            node_ids,
        ).fetchall()
        return [dict(r) for r in rows]

    def memory_entries_with_utility(self):
        rows = self.db.execute(
            "SELECT me.id, me.title, me.content, me.importance, me.access_count, "
            "me.last_accessed, me.is_active, mus.utility_score "
            "FROM memory_entries me "
            "JOIN memory_utility_scores mus ON me.id=mus.memory_entry_id "
            "WHERE me.is_active=1"
        ).fetchall()
        return [dict(r) for r in rows]


class SleepConsolidationLogsRepository(BaseRepository):
    """休眠巩固日志表。"""

    def __init__(self, db):
        super().__init__(db, "sleep_consolidation_logs", TABLE_SLEEP_CONSOLIDATION_LOGS_COLS)

    def list_recent(self, limit=10):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
