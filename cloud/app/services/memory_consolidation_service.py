import json
import uuid
from datetime import datetime, timedelta

from cloud.app.repositories import (
    EpisodicMemoryRepository,
    KgEntitiesRepository,
    MemoryConsolidationLogRepository,
)
from cloud.app.services.base import BaseService


def _calc_utility(valence: float, intensity: float) -> float:
    return valence * intensity


class MemoryConsolidationService(BaseService):
    def trigger_consolidation(self, triggered_by: str) -> dict:
        started = datetime.now()
        ep_repo = EpisodicMemoryRepository(self.db)
        kg_repo = KgEntitiesRepository(self.db)
        log_repo = MemoryConsolidationLogRepository(self.db)

        rows = ep_repo.find_unconsolidated()
        if not rows:
            return {"promoted": 0, "pruned": 0, "total": 0}

        scored = [
            (r, _calc_utility(r["valence"] or 0.0, r["intensity"] or 0.5)) for r in rows
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        total = len(scored)
        top_n = min(20, total)
        promoted = 0
        for i in range(top_n):
            item = scored[i][0]
            name = item.get("title") or item.get("event_type") or f"memory:{item['id']}"
            entity_id = f"mem:{uuid.uuid4()}"
            kg_repo.create(
                {
                    "entity_id": entity_id,
                    "entity_type": "memory",
                    "name": name,
                    "source_table": "episodic_memory",
                    "source_row_id": item["id"],
                    "status": "active",
                    "confidence": 1.0,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            promoted += 1

        pruned = 0
        if total > top_n:
            midpoint = total // 2
            for i in range(midpoint, total):
                if scored[i][0].get("valence", 0) < 0:
                    pruned += 1

        duration_ms = int((datetime.now() - started).total_seconds() * 1000)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_repo.create(
            {
                "consolidation_type": "sleep_consolidation",
                "source_table": "episodic_memory",
                "item_count": total,
                "items_promoted": promoted,
                "items_pruned": pruned,
                "duration_ms": duration_ms,
                "status": "completed",
                "details": json.dumps(
                    {"triggered_by": triggered_by}, ensure_ascii=False
                ),
                "created_at": now,
            }
        )
        return {"promoted": promoted, "pruned": pruned, "total": total}

    def consolidation_status(self) -> list:
        log_repo = MemoryConsolidationLogRepository(self.db)
        return log_repo.list_recent(limit=5)

    def evaluate_memory(self, agent_id: str) -> dict:
        ep_repo = EpisodicMemoryRepository(self.db)
        log_repo = MemoryConsolidationLogRepository(self.db)

        now = datetime.now()
        seven_days_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")

        ep_count = ep_repo.count_by_creator(agent_id)

        ret_count = log_repo.count_by_type_since(
            "retrieval_reconsolidation", seven_days_ago
        )

        con_logs = log_repo.count_by_type_since("sleep_consolidation", seven_days_ago)
        con_rate = min(1.0, con_logs / 7.0) if con_logs else 0.0

        ret_norm = min(1.0, ret_count / 50.0)
        cov_norm = min(1.0, ep_count / 200.0)
        decay_norm = max(0.0, 1.0 - ep_count / 500.0) if ep_count else 1.0

        composite = round(
            0.4 * con_rate + 0.3 * ret_norm + 0.2 * cov_norm - 0.1 * decay_norm, 4
        )

        return {
            "agent_id": agent_id,
            "episodic_count": ep_count,
            "retrievals_7d": ret_count,
            "consolidation_rate": round(con_rate, 4),
            "composite_score": max(0.0, composite),
        }

    def evaluate_trend(self) -> dict:
        log_repo = MemoryConsolidationLogRepository(self.db)
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime(
            "%Y-%m-%d 00:00:00"
        )
        rows = log_repo.trend_since(seven_days_ago)

        trend: dict[str, dict[str, int]] = {}
        for r in rows:
            day = r["day"]
            if day not in trend:
                trend[day] = {}
            trend[day][r["consolidation_type"]] = r["cnt"]

        return {"trend_by_day": trend}
