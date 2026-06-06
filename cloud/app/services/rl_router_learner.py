"""路由学习器，负责任务路由匹配、结果记录与路由策略统计。"""

import json

from cloud.app.services.base import BaseService


class RouterLearner(BaseService):
    """RouterLearner 服务类。"""

    def route_task(self, task_type: str, task_content: str, source: str) -> dict:
        """route_task 操作。

        Args:
            task_type: 描述
            task_content: 描述
            source: 描述

        Returns:
            描述
        """
        rows = self.db.execute("SELECT * FROM routing_strategies WHERE is_active=1 ORDER BY priority ASC").fetchall()

        matched = []
        for row in rows:
            pattern = row["task_type_pattern"]
            if not pattern or pattern == "%":
                matched.append((row, self._score_strategy(row)))
                continue
            like_pattern = pattern.replace("%", "%").replace("_", "_")
            check = self.db.execute("SELECT ? LIKE ?", (task_type, like_pattern)).fetchone()[0]
            if check:
                matched.append((row, self._score_strategy(row)))

        if not matched:
            return {
                "strategy_key": None,
                "route_to": None,
                "strategy_name": "no_match",
                "confidence": 0.0,
                "task_type": task_type,
                "source": source,
            }

        matched.sort(key=lambda x: (-x[1], x[0]["priority"]))
        best = matched[0][0]

        condition_rules = json.loads(best["condition_rules"]) if best["condition_rules"] else {}
        extra = {}
        if condition_rules.get("require_keyword"):
            extra["keyword_match"] = condition_rules["require_keyword"] in (task_content or "")

        total = best["success_count"] + best["fail_count"]
        success_rate = best["success_count"] / total if total > 0 else 0.5

        return {
            "strategy_key": best["strategy_key"],
            "strategy_name": best["name"],
            "route_to": best["route_to"],
            "confidence": round(success_rate, 4),
            "priority": best["priority"],
            "task_type": task_type,
            "source": source,
            "extra": extra,
        }

    def log_result(
        self,
        task_id: str,
        task_type: str,
        source: str,
        strategy_used: str,
        routed_to: str,
        duration_ms: int,
        success: int,
    ) -> dict:
        """log_result 操作。

        Args:
            task_id: 描述
            task_type: 描述
            source: 描述
            strategy_used: 描述
            routed_to: 描述
            duration_ms: 描述
            success: 描述

        Returns:
            描述
        """
        self.db.execute(
            "INSERT INTO routing_log (task_id, task_type, source, strategy_used, routed_to, duration_ms, success) VALUES (?,?,?,?,?,?,?)",
            (task_id, task_type, source, strategy_used, routed_to, duration_ms, success),
        )

        row = self.db.execute("SELECT * FROM routing_strategies WHERE strategy_key=?", (strategy_used,)).fetchone()
        if row:
            if success:
                new_success = row["success_count"] + 1
                new_fail = row["fail_count"]
            else:
                new_success = row["success_count"]
                new_fail = row["fail_count"] + 1
            total = new_success + new_fail
            old_avg = row["avg_duration_ms"]
            new_avg = (old_avg * (total - 1) + duration_ms) / total if total > 0 else float(duration_ms)
            self.db.execute(
                "UPDATE routing_strategies SET success_count=?, fail_count=?, avg_duration_ms=?, updated_at=CURRENT_TIMESTAMP WHERE strategy_key=?",
                (new_success, new_fail, round(new_avg, 2), strategy_used),
            )

        self.db.commit()
        return {"task_id": task_id, "logged": True}

    def get_stats(self, task_type: str = None) -> dict:
        """获取统计。

        Args:
            task_type: 描述

        Returns:
            描述
        """
        if task_type:
            rows = self.db.execute(
                "SELECT strategy_used, COUNT(*) as total, "
                "SUM(success) as success_count, "
                "AVG(CASE WHEN success=1 THEN duration_ms ELSE NULL END) as avg_success_duration_ms, "
                "AVG(duration_ms) as avg_duration_ms "
                "FROM routing_log WHERE task_type=? "
                "GROUP BY strategy_used ORDER BY total DESC",
                (task_type,),
            ).fetchall()
        else:
            rows = self.db.execute(
                "SELECT strategy_used, COUNT(*) as total, "
                "SUM(success) as success_count, "
                "AVG(CASE WHEN success=1 THEN duration_ms ELSE NULL END) as avg_success_duration_ms, "
                "AVG(duration_ms) as avg_duration_ms "
                "FROM routing_log GROUP BY strategy_used ORDER BY total DESC"
            ).fetchall()

        stats = []
        for r in rows:
            total = r["total"]
            success = r["success_count"] or 0
            stats.append(
                {
                    "strategy_used": r["strategy_used"],
                    "total": total,
                    "success_count": success,
                    "fail_count": total - success,
                    "success_rate": round(success / total, 4) if total > 0 else 0.0,
                    "avg_duration_ms": round(r["avg_duration_ms"] or 0.0, 2),
                    "avg_success_duration_ms": round(r["avg_success_duration_ms"] or 0.0, 2),
                }
            )

        return {"stats": stats, "task_type": task_type or "all"}

    def get_strategies(self, task_type: str = None) -> list:
        """get_strategies 操作。

        Args:
            task_type: 描述

        Returns:
            描述
        """
        if task_type:
            like_pattern = task_type.replace("%", "%").replace("_", "_")
            rows = self.db.execute(
                "SELECT * FROM routing_strategies WHERE is_active=1 AND (task_type_pattern='%' OR ? LIKE task_type_pattern) ORDER BY priority ASC",
                (like_pattern,),
            ).fetchall()
        else:
            rows = self.db.execute("SELECT * FROM routing_strategies WHERE is_active=1 ORDER BY priority ASC").fetchall()

        return [dict(r) for r in rows]

    def get_strategy(self, strategy_id: int) -> dict:
        """获取策略。

        Args:
            strategy_id: 描述

        Returns:
            描述
        """
        row = self.db.execute("SELECT * FROM routing_strategies WHERE id=?", (strategy_id,)).fetchone()
        if not row:
            return None
        return dict(row)
