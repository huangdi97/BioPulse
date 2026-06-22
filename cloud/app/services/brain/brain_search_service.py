"""脑搜索服务，提供跨记忆类型的统一检索与相关性排序。"""

from shared.base_service import BaseService
from shared.datetime_utils import now as _now


class BrainSearchService(BaseService):
    """BrainSearch 服务类。"""

    def _calc_search_relevance(self, query: str, row: dict, source: str) -> float:
        q = query.lower()
        score = 0.5
        score += self._match_keyword_bonus(q, row, source)
        score += self._numeric_bonus(row, source)
        return round(min(score, 1.0), 4)

    def _match_keyword_bonus(self, q: str, row: dict, source: str) -> float:
        if source == "episodic":
            bonus = 0.0
            if q in (row.get("title") or "").lower():
                bonus += 0.4
            if q in (row.get("description") or "").lower():
                bonus += 0.2
            return bonus
        elif source == "procedural":
            if q in (row.get("name") or "").lower():
                return 0.4
        elif source == "working_memory":
            if q in (row.get("slot_key") or "").lower():
                return 0.4
        elif source == "kg_entities":
            if q in (row.get("name") or "").lower():
                return 0.4
        return 0.0

    def _numeric_bonus(self, row: dict, source: str) -> float:
        if source == "episodic":
            return (row.get("intensity") or 0) * 0.3
        elif source == "sensory":
            return (row.get("importance") or 0) * 0.5
        elif source == "procedural":
            return min((row.get("invocation_count") or 0) * 0.01, 0.3)
        elif source == "working_memory":
            return min((row.get("ttl_seconds") or 0) * 0.0001, 0.3)
        elif source == "kg_entities":
            return (row.get("confidence") or 0) * 0.3
        return 0.0

    def _parse_query(self, query: str, memory_types: list[str] | None) -> tuple[str, str, list[str], str]:
        if memory_types is None:
            memory_types = ["episodic", "sensory", "procedural", "working_memory", "kg_entities"]
        pattern = f"%{query}%"
        n = _now()
        return query, pattern, memory_types, n

    def _execute_search(self, query: str, pattern: str, memory_types: list[str], n: str, limit: int) -> list[dict]:
        queries = {
            "episodic": (
                "SELECT *, 'episodic' AS _source FROM episodic_memory WHERE title LIKE ? OR description LIKE ? OR context LIKE ? OR outcome LIKE ? ORDER BY intensity DESC LIMIT ?",
                [pattern] * 4 + [limit],
            ),
            "sensory": (
                "SELECT *, 'sensory' AS _source FROM sensory_memory WHERE raw_content LIKE ? AND (expires_at = '' OR expires_at > ?) ORDER BY importance DESC LIMIT ?",
                [pattern, n, limit],
            ),
            "procedural": (
                "SELECT *, 'procedural' AS _source FROM procedural_memory WHERE name LIKE ? OR description LIKE ? OR steps LIKE ? OR trigger_conditions LIKE ? ORDER BY invocation_count DESC LIMIT ?",
                [pattern] * 4 + [limit],
            ),
            "working_memory": (
                "SELECT *, 'working_memory' AS _source FROM working_memory WHERE (slot_key LIKE ? OR slot_value LIKE ?) AND expires_at > ? ORDER BY ttl_seconds DESC LIMIT ?",
                [pattern, pattern, n, limit],
            ),
            "kg_entities": (
                "SELECT *, 'kg_entities' AS _source FROM kg_entities WHERE name LIKE ? OR entity_type LIKE ? OR aliases LIKE ? ORDER BY confidence DESC LIMIT ?",
                [pattern] * 3 + [limit],
            ),
        }
        results = []
        for mt in memory_types:
            if mt not in queries:
                continue
            sql, params = queries[mt]
            rows = self.db.execute(sql, tuple(params)).fetchall()
            for r in rows:
                d = dict(r)
                d["relevance"] = self._calc_search_relevance(query, d, mt)
                results.append(d)
        return results

    def _rank_results(self, results: list[dict], limit: int) -> dict:
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return {"results": results[:limit], "total": len(results)}

    def unified_search(self, query: str, memory_types: list[str] | None = None, limit: int = 20) -> dict:
        query, pattern, memory_types, n = self._parse_query(query, memory_types)
        results = self._execute_search(query, pattern, memory_types, n, limit)
        return self._rank_results(results, limit)
