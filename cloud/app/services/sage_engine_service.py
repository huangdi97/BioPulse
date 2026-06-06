"""Sage 引擎服务，负责多维记忆评分与热温冷分层进化管理。"""

import json
from datetime import datetime

from cloud.app.repositories.sage_repository import SageRepository
from cloud.app.research_database import get_research_db
from cloud.app.services.brain_evolution_service import BrainEvolutionService
from cloud.app.services.brain_memory_service import BrainMemoryService
from cloud.app.services.memory_consolidation_service import MemoryConsolidationService
from cloud.app.services.sage_linking import SageLinkingService
from cloud.app.services.sage_scoring import (
    determine_tier,
    normalize,
    score_episodic,
    score_procedural,
    score_semantic,
    score_world_tree,
    ts_to_epoch,
)


class SageEngineService:
    """Sage 引擎服务，提供多维记忆评分、热温冷分层与记忆进化管理。"""

    def __init__(self, db=None):
        self.db = db or get_research_db()
        self.repo = SageRepository(self.db)
        self.linking = SageLinkingService(db)

    def _normalize(self, value, min_val, max_val) -> float:
        return normalize(value, min_val, max_val)

    @staticmethod
    def _ts_to_epoch(ts_str):
        return ts_to_epoch(ts_str)

    @staticmethod
    def _determine_tier(score):
        return determine_tier(score)

    def _score_episodic(self, bms, tier_dist, comp):
        return score_episodic(self.repo, bms, tier_dist, comp)

    def _score_semantic(self, bms, tier_dist, comp):
        return score_semantic(self.repo, bms, tier_dist, comp)

    def _score_procedural(self, bms, tier_dist, comp):
        return score_procedural(self.repo, bms, tier_dist, comp)

    def _score_world_tree(self, tier_dist, comp):
        return score_world_tree(self.repo, self.db, tier_dist, comp)

    def score_all_memories(self) -> dict:
        now = datetime.now().isoformat()
        tier_dist = {"hot": 0, "warm": 0, "cold": 0}
        comp = {"brain_memory": 0, "world_tree": 0}

        bms = BrainMemoryService(db=self.db)
        total = 0
        total += self._score_episodic(bms, tier_dist, comp)
        total += self._score_semantic(bms, tier_dist, comp)
        total += self._score_procedural(bms, tier_dist, comp)
        total += self._score_world_tree(tier_dist, comp)

        return {
            "total_scored": total,
            "tier_distribution": tier_dist,
            "by_component": comp,
            "last_scored_at": now,
        }

    def score_detail(self, memory_type, memory_id) -> dict | None:
        row = self.repo.get_score(memory_type, memory_id)
        if not row:
            return None

        logs = self.repo.get_recent_logs(limit=20)
        related = [entry for entry in logs if entry.get("memory_type") == memory_type and entry.get("memory_id") == memory_id]

        af_raw = row.get("access_count", 0) or 0
        util = row.get("utility_score", 0.5) or 0.5
        conf = row.get("confidence", 0.5) or 0.5
        breakdown = {
            "access_frequency_raw": af_raw,
            "access_frequency_contribution": min(af_raw, 1.0) * 30,
            "recency_contribution": 20,
            "utility_contribution": util * 30,
            "confidence_contribution": conf * 20,
        }

        return {
            "score": row,
            "breakdown": breakdown,
            "evolution_logs": related,
        }

    def evolve(self, triggered_by="manual") -> dict:
        start = datetime.now()
        result = self.score_all_memories()
        cold_count = 0
        warm_count = 0
        hot_count = 0

        mcs = MemoryConsolidationService(db=self.db)
        bes = BrainEvolutionService(db=self.db)

        cold_scores = self.repo.get_scores_by_tier("cold")
        for cs in cold_scores:
            try:
                mt = cs["memory_type"]
                mid = cs["memory_id"]
                row = self.db.execute(
                    "SELECT COUNT(*) as cnt FROM sage_evolution_log WHERE memory_type=? AND memory_id=? AND action IN ('consolidate','fold')",
                    (mt, mid),
                ).fetchone()
                if row and row["cnt"] >= 3:
                    continue

                if mt == "episodic":
                    mcs.trigger_consolidation(triggered_by=triggered_by)
                    self.repo.log_evolution(
                        triggered_by,
                        "consolidate",
                        mt,
                        mid,
                        json.dumps({"status": "triggered"}),
                    )
                elif mt in ("semantic", "procedural"):
                    bes.fold_memories([mid])
                    self.repo.log_evolution(
                        triggered_by,
                        "fold",
                        mt,
                        mid,
                        json.dumps({"status": "folded"}),
                    )
                else:
                    self.repo.log_evolution(
                        triggered_by,
                        "skip",
                        mt,
                        mid,
                        json.dumps({"status": "unhandled_type"}),
                    )
                cold_count += 1
            except Exception:
                continue

        warm_scores = self.repo.get_scores_by_tier("warm")
        for ws in warm_scores:
            try:
                mt = ws["memory_type"]
                mid = ws["memory_id"]
                ev_row = self.db.execute(
                    "SELECT COUNT(*) as cnt FROM sage_evolution_log WHERE memory_type=? AND memory_id=? AND action='evolve'",
                    (mt, mid),
                ).fetchone()
                ev_count = ev_row["cnt"] if ev_row else 0
                if ev_count % 3 == 0:
                    bes.evolve_memory(mid, "[auto-evolution]", memory_type=mt)
                    self.repo.log_evolution(
                        triggered_by,
                        "evolve",
                        mt,
                        mid,
                        json.dumps({"status": "evolved"}),
                    )
                    warm_count += 1
            except Exception:
                continue

        hot_scores = self.repo.get_scores_by_tier("hot")
        for hs in hot_scores:
            try:
                mt = hs["memory_type"]
                mid = hs["memory_id"]
                self.repo.upsert_score(
                    mt,
                    mid,
                    hs["component"],
                    hs["score"],
                    hs["tier"],
                    access_count=hs["access_count"],
                    last_access=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    utility_score=hs["utility_score"],
                    confidence=hs["confidence"],
                )
                hot_count += 1
            except Exception:
                continue

        duration_ms = int((datetime.now() - start).total_seconds() * 1000)
        return {
            "triggered_by": triggered_by,
            "scored_count": result["total_scored"],
            "cold_consolidated": cold_count,
            "warm_evolved": warm_count,
            "hot_refreshed": hot_count,
            "total_processed": cold_count + warm_count + hot_count,
            "duration_ms": duration_ms,
        }
