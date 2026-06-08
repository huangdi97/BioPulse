"""Sage 引擎缓存模块，提供评分查询与分解。"""


class SageCacheMixin:
    """评分缓存混入类，提供记忆评分解构查询。"""

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
