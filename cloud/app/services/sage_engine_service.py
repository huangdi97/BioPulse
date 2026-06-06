"""Sage 引擎服务，负责多维记忆评分与热温冷分层进化管理。"""

import json
from datetime import datetime

from cloud.app.repositories.memory_repository import NodeMemoryLinksRepository
from cloud.app.repositories.sage_repository import SageRepository
from cloud.app.repositories.world_tree_repository import WorldTreeNodesRepository
from cloud.app.research_database import get_research_db
from cloud.app.services.brain_evolution_service import BrainEvolutionService
from cloud.app.services.brain_memory_service import BrainMemoryService
from cloud.app.services.memory_consolidation_service import MemoryConsolidationService
from cloud.app.services.sage_linking import SageLinkingService


class SageEngineService:
    """Sage 引擎服务，提供多维记忆评分、热温冷分层与记忆进化管理。"""

    def __init__(self, db=None):
        self.db = db or get_research_db()
        self.repo = SageRepository(self.db)
        self.linking = SageLinkingService(db)

    def _normalize(self, value, min_val, max_val) -> float:
        if max_val <= min_val:
            return 0.0
        return (value - min_val) / (max_val - min_val)

    @staticmethod
    def _ts_to_epoch(ts_str):
        try:
            return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").timestamp()
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _determine_tier(score):
        if score >= 70:
            return "hot"
        if score >= 30:
            return "warm"
        return "cold"

    def _score_episodic(self, bms, tier_dist, comp):
        count = 0
        ep_res = bms.episodic_list(page=1, page_size=1000)
        items = ep_res.get("items", [])
        if not items:
            return count

        ts_list = [it.get("created_at", "") for it in items]
        min_e = self._ts_to_epoch(min(ts_list))
        max_e = self._ts_to_epoch(max(ts_list))
        rng = max_e - min_e

        for it in items:
            mid = it["id"]
            ts = it.get("created_at", "")
            recency = ((self._ts_to_epoch(ts) - min_e) / rng) if rng > 0 else 0.5
            utility = abs(it.get("valence", 0) or 0)
            score = (recency * 0.2 + utility * 0.3 + 0.5 * 0.2) * 100
            tier = self._determine_tier(score)
            self.repo.upsert_score(
                "episodic",
                mid,
                "brain_memory",
                round(score, 2),
                tier,
                access_count=0,
                last_access=ts,
                utility_score=round(utility, 4),
                confidence=0.5,
            )
            count += 1
            tier_dist[tier] += 1
            comp["brain_memory"] += 1
        return count

    def _score_semantic(self, bms, tier_dist, comp):
        count = 0
        sem_res = bms.semantic_search("", limit=1000)
        items = sem_res.get("items", [])
        if not items:
            return count

        ts_list = [it.get("last_accessed") or it.get("created_at", "") for it in items]
        min_e = self._ts_to_epoch(min(ts_list))
        max_e = self._ts_to_epoch(max(ts_list))
        rng = max_e - min_e
        ac_vals = [it.get("access_count", 0) or 0 for it in items]
        ac_min, ac_max = min(ac_vals), max(ac_vals)

        for it in items:
            mid = it["id"]
            ts = it.get("last_accessed") or it.get("created_at", "")
            recency = ((self._ts_to_epoch(ts) - min_e) / rng) if rng > 0 else 0.5
            af = self._normalize(it.get("access_count", 0) or 0, ac_min, ac_max)
            utility = it.get("importance", 0.5) or 0.5
            score = (af * 0.3 + recency * 0.2 + utility * 0.3 + 0.5 * 0.2) * 100
            tier = self._determine_tier(score)
            self.repo.upsert_score(
                "semantic",
                mid,
                "brain_memory",
                round(score, 2),
                tier,
                access_count=it.get("access_count", 0) or 0,
                last_access=ts,
                utility_score=round(utility, 4),
                confidence=0.5,
            )
            count += 1
            tier_dist[tier] += 1
            comp["brain_memory"] += 1
        return count

    def _score_procedural(self, bms, tier_dist, comp):
        count = 0
        proc_res = bms.procedural_recall("")
        items = proc_res.get("items", [])
        for it in items:
            mid = it["id"]
            utility = it.get("success_rate", 0.5) or 0.5
            score = (utility * 0.3 + 0.5 * 0.2) * 100
            tier = self._determine_tier(score)
            self.repo.upsert_score(
                "procedural",
                mid,
                "brain_memory",
                round(score, 2),
                tier,
                access_count=0,
                last_access="",
                utility_score=round(utility, 4),
                confidence=0.5,
            )
            count += 1
            tier_dist[tier] += 1
            comp["brain_memory"] += 1
        return count

    def _score_world_tree(self, tier_dist, comp):
        count = 0
        wt_repo = WorldTreeNodesRepository(self.db)
        nml_repo = NodeMemoryLinksRepository(self.db)
        nodes = wt_repo.list_active_sorted()
        if not nodes:
            return count

        child_counts = {}
        for n in nodes:
            pid = n.get("parent_id")
            if pid is not None:
                child_counts[pid] = child_counts.get(pid, 0) + 1

        for n in nodes:
            mid = n["id"]
            cc = child_counts.get(mid, 0)
            depth = n.get("level", 0) or 0
            linked = nml_repo.count_by_node(mid)
            score = min(100, cc * 10 + linked * 5 + depth)
            tier = self._determine_tier(score)
            self.repo.upsert_score(
                "world_tree_node",
                mid,
                "world_tree",
                round(score, 2),
                tier,
                access_count=0,
                last_access=n.get("updated_at", ""),
                utility_score=0.5,
                confidence=0.5,
            )
            count += 1
            tier_dist[tier] += 1
            comp["world_tree"] += 1
        return count

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
