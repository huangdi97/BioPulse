"""记忆效用排名与睡眠巩固模块，支持按效用评分排序记忆，以及合并、归档、剪枝等巩固操作。"""

import json
from datetime import datetime

from cloud.app.repositories import (
    MemoryEntriesRepository,
    MemoryUtilityScoresRepository,
    NodeMemoryLinksRepository,
    SleepConsolidationLogsRepository,
)


class UtilityRankerMixin:
    """效用排名混入类，提供排名查询与睡眠巩固操作。"""

    def utility_rankings(self, min_utility: float = 0.0, limit: int = 20) -> list[dict]:
        mus_repo = MemoryUtilityScoresRepository(self._connection())
        return mus_repo.list_ranked(min_utility=min_utility, limit=limit)

    def sleep_consolidate(self) -> dict:
        entry_repo = MemoryEntriesRepository(self._connection())
        log_repo = SleepConsolidationLogsRepository(self._connection())
        link_repo = NodeMemoryLinksRepository(self._connection())

        rows = link_repo.memory_entries_with_utility()
        archived = merged = promoted = pruned = 0
        now = self._now()
        for r in rows:
            u = r["utility_score"]
            mid = r["id"]
            if u < 0.2:
                self._do_archive(entry_repo, log_repo, mid, u, now)
                archived += 1
            elif u >= 0.8:
                if self._do_merge(entry_repo, log_repo, r, mid, u, now):
                    merged += 1
            elif u >= 0.6:
                self._do_promote(entry_repo, log_repo, r, mid, now)
                promoted += 1
            elif 0.2 <= u < 0.6:
                if self._do_prune_log(log_repo, r, mid, u, now):
                    pruned += 1
        self.db.commit()
        return {
            "archived": archived,
            "merged": merged,
            "promoted": promoted,
            "prune_candidates_logged": pruned,
        }

    def sleep_history(self) -> list[dict]:
        log_repo = SleepConsolidationLogsRepository(self._connection())
        return log_repo.list_recent(limit=10)

    def _do_archive(self, entry_repo, log_repo, mid, u, now):
        entry_repo.deactivate(mid, now)
        log_repo.create(
            {
                "consolidation_type": "archive",
                "source_entry_ids": json.dumps([mid]),
                "target_entry_id": None,
                "action_detail": f"Archived: utility={u:.4f}",
                "utility_before": u,
                "utility_after": 0.0,
                "created_at": now,
            }
        )

    def _do_merge(self, entry_repo, log_repo, r, mid, u, now):
        prefix = r["title"][:20] if r["title"] else ""
        similar = entry_repo.find_similar_by_title(prefix, mid, min_utility=0.8)
        if not similar:
            return False
        target = similar[0]["id"]
        if r["content"]:
            entry_repo.append_content(r["content"], target, now)
        entry_repo.deactivate(mid, now)
        log_repo.create(
            {
                "consolidation_type": "merge",
                "source_entry_ids": json.dumps([mid]),
                "target_entry_id": target,
                "action_detail": f"Merged into {target}: prefix={prefix}",
                "utility_before": u,
                "utility_after": u,
                "created_at": now,
            }
        )
        return True

    def _do_promote(self, entry_repo, log_repo, r, mid, now):
        new_imp = round(min(r["importance"] + 0.05, 1.0), 4)
        entry_repo.promote_importance(new_imp, mid, now)
        log_repo.create(
            {
                "consolidation_type": "promote",
                "source_entry_ids": json.dumps([mid]),
                "target_entry_id": None,
                "action_detail": f"Promoted: importance {r['importance']} -> {new_imp}",
                "utility_before": r["importance"],
                "utility_after": new_imp,
                "created_at": now,
            }
        )

    def _do_prune_log(self, log_repo, r, mid, u, now):
        if r["last_accessed"]:
            try:
                days_ago = (datetime.now() - datetime.strptime(r["last_accessed"], "%Y-%m-%d %H:%M:%S")).days
            except (ValueError, TypeError):
                days_ago = 999
        else:
            days_ago = 999
        if days_ago > 30 and (r["access_count"] or 0) < 3:
            log_repo.create(
                {
                    "consolidation_type": "prune_log",
                    "source_entry_ids": json.dumps([mid]),
                    "target_entry_id": None,
                    "action_detail": f"Prune candidate: days_ago={days_ago}, access_count={r['access_count']}",
                    "utility_before": u,
                    "utility_after": u,
                    "created_at": now,
                }
            )
            return True
        return False
