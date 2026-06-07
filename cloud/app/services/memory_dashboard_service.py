"""记忆 dashboard 统计服务。"""

import json

from cloud.app.repositories import MemoryEntriesRepository, MemoryRecallLogRepository


class MemoryDashboardService:
    def __init__(self, db):
        self.db = db

    def dashboard(self) -> dict:
        entry_repo = MemoryEntriesRepository(self.db)
        recall_repo = MemoryRecallLogRepository(self.db)
        total = entry_repo.count_active()
        type_rows = entry_repo.by_type_stats()
        by_type = [{"memory_type": r["memory_type"], "count": r["cnt"], "avg_importance": round(r["avg_imp"], 4)} for r in type_rows]
        tag_counter = {}
        entries = entry_repo.all_context_tags_active()
        for e in entries:
            try:
                tags = json.loads(e["context_tags"])
            except (json.JSONDecodeError, TypeError):
                tags = []
            for t in tags:
                tag_counter[t] = tag_counter.get(t, 0) + 1
        top_tags = sorted(tag_counter.items(), key=lambda x: x[1], reverse=True)[:10]
        top_tags = [{"tag": t, "count": c} for t, c in top_tags]
        recent_logs = recall_repo.list_recent(limit=5)
        return {"total_entries": total, "by_memory_type": by_type, "top_context_tags": top_tags, "recent_recall_logs": recent_logs}
