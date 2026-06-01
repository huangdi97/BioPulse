import json
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    MemoryEntriesRepository,
    MemoryUtilityScoresRepository,
    NodeMemoryLinksRepository,
    SleepConsolidationLogsRepository,
    WorldTreeNodesRepository,
    WorldTreeSnapshotsRepository,
)
from cloud.app.services.base import BaseService


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class MemoryUtilityService(BaseService):

    def subtree_stats(self, node_id: int) -> dict:
        tree_repo = WorldTreeNodesRepository(self.db)
        link_repo = NodeMemoryLinksRepository(self.db)

        if not tree_repo.exists_by_id(node_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Node not found")
        desc_ids = tree_repo.descendant_ids(node_id)
        if not desc_ids:
            return {"total_nodes": 0, "max_depth": 0, "total_memories": 0,
                    "avg_importance": 0.0, "by_level": []}
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
            "total_nodes": len(desc_ids), "max_depth": max_depth,
            "total_memories": total_memories, "avg_importance": avg_importance,
            "by_level": by_level,
        }

    def move_node(self, node_id: int, new_parent_id: Optional[int]) -> dict:
        tree_repo = WorldTreeNodesRepository(self.db)
        node = tree_repo.get_by_id(node_id)
        if not node:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Node not found")
        if new_parent_id is not None:
            if not tree_repo.exists_by_id(new_parent_id):
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Parent node not found")
            desc = tree_repo.descendant_ids(node_id)
            if new_parent_id in desc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Cannot move a node into its own descendant")
        now = _now()
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
        tree_repo.update_path(node_id, path, level, _now())

    def _refresh_children(self, tree_repo: WorldTreeNodesRepository, parent_id: int) -> None:
        for child in self.db.execute(
            f"SELECT id FROM {tree_repo.table_name} WHERE parent_id=?", (parent_id,)
        ).fetchall():
            self._refresh_path(tree_repo, child["id"])
            self._refresh_children(tree_repo, child["id"])

    def tree_heatmap(self) -> list[dict]:
        tree_repo = WorldTreeNodesRepository(self.db)
        link_repo = NodeMemoryLinksRepository(self.db)

        rows = tree_repo.list_active_sorted()
        result = []
        for r in rows:
            mc = link_repo.count_by_node(r["id"])
            result.append({"name": r["name"], "level": r["level"], "memory_count": mc})
        return result

    def tree_duplicates(self, node_id: int) -> list[dict]:
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
        return {"deleted_count": deleted, "message": f"Pruned {deleted} inactive nodes and their links"}

    def _calc_utility(self, entry: dict, conn_count: int) -> dict:
        imp = entry["importance"] or 0.0
        ac = entry["access_count"] or 0
        la = entry["last_accessed"]
        access_freq = min(ac / 100.0, 1.0)
        if la is None:
            recency = 0.2
        else:
            try:
                days_ago = (datetime.now() - datetime.strptime(la, "%Y-%m-%d %H:%M:%S")).days
            except (ValueError, TypeError):
                days_ago = 999
            recency = 1.0 if days_ago <= 7 else (0.5 if days_ago <= 30 else 0.2)
        connectivity = min(conn_count / 5.0, 1.0)
        utility = round(0.3 * imp + 0.3 * access_freq + 0.2 * recency + 0.2 * connectivity, 4)
        return {
            "utility_score": utility, "access_frequency": access_freq,
            "recency_score": recency, "importance_score": imp,
            "connectivity_score": connectivity, "decay_rate": round(1.0 - utility, 4),
        }

    def score_memory(self, memory_id: int) -> dict:
        entry_repo = MemoryEntriesRepository(self.db)
        mus_repo = MemoryUtilityScoresRepository(self.db)
        link_repo = NodeMemoryLinksRepository(self.db)

        entry = entry_repo.find_active_by_id(memory_id)
        if not entry:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Memory entry not found")
        conn_count = link_repo.count_by_node(memory_id)
        u = self._calc_utility(entry, conn_count)
        now = _now()
        mus_repo.upsert_score({
            "memory_entry_id": memory_id, "utility_score": u["utility_score"],
            "access_frequency": u["access_frequency"], "recency_score": u["recency_score"],
            "importance_score": u["importance_score"], "connectivity_score": u["connectivity_score"],
            "decay_rate": u["decay_rate"], "last_utility_update": now, "created_at": now,
        })
        self.db.commit()
        return {"memory_id": memory_id, **u}

    def score_all(self) -> dict:
        entry_repo = MemoryEntriesRepository(self.db)
        mus_repo = MemoryUtilityScoresRepository(self.db)
        link_repo = NodeMemoryLinksRepository(self.db)

        rows = entry_repo.list_active_ordered(order_by="id")
        now = _now()
        processed = 0
        for r in rows:
            conn_count = link_repo.count_by_node(r["id"])
            u = self._calc_utility(r, conn_count)
            mus_repo.upsert_score({
                "memory_entry_id": r["id"], "utility_score": u["utility_score"],
                "access_frequency": u["access_frequency"], "recency_score": u["recency_score"],
                "importance_score": u["importance_score"], "connectivity_score": u["connectivity_score"],
                "decay_rate": u["decay_rate"],
                "last_utility_update": now, "created_at": now,
            })
            processed += 1
        self.db.commit()
        return {"processed_count": processed}

    def utility_rankings(self, min_utility: float = 0.0, limit: int = 20) -> list[dict]:
        mus_repo = MemoryUtilityScoresRepository(self.db)
        return mus_repo.list_ranked(min_utility=min_utility, limit=limit)

    def sleep_consolidate(self) -> dict:
        entry_repo = MemoryEntriesRepository(self.db)
        log_repo = SleepConsolidationLogsRepository(self.db)
        mus_repo = MemoryUtilityScoresRepository(self.db)
        link_repo = NodeMemoryLinksRepository(self.db)

        rows = link_repo.memory_entries_with_utility()
        archived = merged = promoted = pruned = 0
        now = _now()
        for r in rows:
            u = r["utility_score"]
            mid = r["id"]
            if u < 0.2:
                entry_repo.deactivate(mid, now)
                log_repo.create({
                    "consolidation_type": "archive", "source_entry_ids": json.dumps([mid]),
                    "target_entry_id": None, "action_detail": f"Archived: utility={u:.4f}",
                    "utility_before": u, "utility_after": 0.0, "created_at": now,
                })
                archived += 1
            elif u >= 0.8:
                prefix = r["title"][:20] if r["title"] else ""
                similar = entry_repo.find_similar_by_title(prefix, mid, min_utility=0.8)
                if similar:
                    target = similar[0]["id"]
                    if r["content"]:
                        entry_repo.append_content(r["content"], target, now)
                    entry_repo.deactivate(mid, now)
                    log_repo.create({
                        "consolidation_type": "merge", "source_entry_ids": json.dumps([mid]),
                        "target_entry_id": target,
                        "action_detail": f"Merged into {target}: prefix={prefix}",
                        "utility_before": u, "utility_after": u, "created_at": now,
                    })
                    merged += 1
            elif u >= 0.6:
                new_imp = round(min(r["importance"] + 0.05, 1.0), 4)
                entry_repo.promote_importance(new_imp, mid, now)
                log_repo.create({
                    "consolidation_type": "promote", "source_entry_ids": json.dumps([mid]),
                    "target_entry_id": None,
                    "action_detail": f"Promoted: importance {r['importance']} -> {new_imp}",
                    "utility_before": r["importance"], "utility_after": new_imp, "created_at": now,
                })
                promoted += 1
            elif 0.2 <= u < 0.6:
                if r["last_accessed"]:
                    try:
                        days_ago = (datetime.now() - datetime.strptime(r["last_accessed"], "%Y-%m-%d %H:%M:%S")).days
                    except (ValueError, TypeError):
                        days_ago = 999
                else:
                    days_ago = 999
                if days_ago > 30 and (r["access_count"] or 0) < 3:
                    log_repo.create({
                        "consolidation_type": "prune_log", "source_entry_ids": json.dumps([mid]),
                        "target_entry_id": None,
                        "action_detail": f"Prune candidate: days_ago={days_ago}, access_count={r['access_count']}",
                        "utility_before": u, "utility_after": u, "created_at": now,
                    })
                    pruned += 1
        self.db.commit()
        return {"archived": archived, "merged": merged, "promoted": promoted,
                "prune_candidates_logged": pruned}

    def sleep_history(self) -> list[dict]:
        log_repo = SleepConsolidationLogsRepository(self.db)
        return log_repo.list_recent(limit=10)
