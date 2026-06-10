"""脑搜索服务，提供跨记忆类型的统一检索与相关性排序。"""

from shared.base_service import BaseService


def _now() -> str:
    """return datetime.now().strftime("%Y-%m-%d %H:%M:%S")"""


class BrainSearchService(BaseService):
    """BrainSearch 服务类。"""

    def _calc_search_relevance(self, query: str, row: dict, source: str) -> float:
        q = query.lower()
        score = 0.5
        if source == "episodic":
            if q in (row.get("title") or "").lower():
                score += 0.4
            if q in (row.get("description") or "").lower():
                score += 0.2
            score += (row.get("intensity") or 0) * 0.3
        elif source == "sensory":
            score += (row.get("importance") or 0) * 0.5
        elif source == "procedural":
            if q in (row.get("name") or "").lower():
                score += 0.4
            score += min((row.get("invocation_count") or 0) * 0.01, 0.3)
        elif source == "working_memory":
            if q in (row.get("slot_key") or "").lower():
                score += 0.4
            score += min((row.get("ttl_seconds") or 0) * 0.0001, 0.3)
        elif source == "kg_entities":
            if q in (row.get("name") or "").lower():
                score += 0.4
            score += (row.get("confidence") or 0) * 0.3
        return round(min(score, 1.0), 4)

    def unified_search(self, query: str, memory_types: list[str] | None = None, limit: int = 20) -> dict:
        """unified_search 操作。

        Args:
            query: 描述
            memory_types: 描述
            limit: 描述

        Returns:
            描述
        """
        if memory_types is None:
            memory_types = ["episodic", "sensory", "procedural", "working_memory", "kg_entities"]
        pattern = f"%{query}%"
        n = _now()
        results = []

        if "episodic" in memory_types:
            rows = self.db.execute(
                "SELECT *, 'episodic' AS _source FROM episodic_memory WHERE title LIKE ? OR description LIKE ? OR context LIKE ? OR outcome LIKE ? ORDER BY intensity DESC LIMIT ?",
                (pattern, pattern, pattern, pattern, limit),
            ).fetchall()
            for r in rows:
                d = dict(r)
                d["relevance"] = self._calc_search_relevance(query, d, "episodic")
                results.append(d)

        if "sensory" in memory_types:
            rows = self.db.execute(
                "SELECT *, 'sensory' AS _source FROM sensory_memory WHERE raw_content LIKE ? AND (expires_at = '' OR expires_at > ?) ORDER BY importance DESC LIMIT ?",
                (pattern, n, limit),
            ).fetchall()
            for r in rows:
                d = dict(r)
                d["relevance"] = self._calc_search_relevance(query, d, "sensory")
                results.append(d)

        if "procedural" in memory_types:
            rows = self.db.execute(
                "SELECT *, 'procedural' AS _source FROM procedural_memory WHERE name LIKE ? OR description LIKE ? OR steps LIKE ? OR trigger_conditions LIKE ? ORDER BY invocation_count DESC LIMIT ?",
                (pattern, pattern, pattern, pattern, limit),
            ).fetchall()
            for r in rows:
                d = dict(r)
                d["relevance"] = self._calc_search_relevance(query, d, "procedural")
                results.append(d)

        if "working_memory" in memory_types:
            rows = self.db.execute(
                "SELECT *, 'working_memory' AS _source FROM working_memory WHERE (slot_key LIKE ? OR slot_value LIKE ?) AND expires_at > ? ORDER BY ttl_seconds DESC LIMIT ?",
                (pattern, pattern, n, limit),
            ).fetchall()
            for r in rows:
                d = dict(r)
                d["relevance"] = self._calc_search_relevance(query, d, "working_memory")
                results.append(d)

        if "kg_entities" in memory_types:
            rows = self.db.execute(
                "SELECT *, 'kg_entities' AS _source FROM kg_entities WHERE name LIKE ? OR entity_type LIKE ? OR aliases LIKE ? ORDER BY confidence DESC LIMIT ?",
                (pattern, pattern, pattern, limit),
            ).fetchall()
            for r in rows:
                d = dict(r)
                d["relevance"] = self._calc_search_relevance(query, d, "kg_entities")
                results.append(d)

        results.sort(key=lambda x: x["relevance"], reverse=True)
        return {"results": results[:limit], "total": len(results)}
