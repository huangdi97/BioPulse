import json

from cloud.app.services.base import BaseService
from shared.config import settings


class RLRoutingService(BaseService):
    """RLRouting 服务类。"""

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

    def _load_pareto_objectives(self) -> dict:
        """从配置加载帕累托优化目标定义，并校验方向合法性。

        Returns:
            dict: 以目标名称为键，值为 {"direction": "maximize"/"minimize", "weight": float} 的字典。
        """
        objectives = settings.PARETO_OBJECTIVES or {}
        if not objectives:
            return {
                "success_rate": {"direction": "maximize", "weight": 1.0},
                "avg_duration_ms": {"direction": "minimize", "weight": 1.0},
                "load": {"direction": "minimize", "weight": 0.5},
            }
        for obj_name, obj_cfg in objectives.items():
            direction = obj_cfg.get("direction")
            if direction not in ("maximize", "minimize"):
                raise ValueError(f"Pareto objective '{obj_name}' direction must be 'maximize' or 'minimize', got '{direction}'")
        return objectives

    def _dominates(self, a: dict, b: dict, objectives: dict) -> bool:
        """判断解 a 是否帕累托支配解 b（a 在所有目标上不差于 b，且至少在一个目标上严格优于 b）。"""
        at_least_as_good = True
        strictly_better = 0
        for name, cfg in objectives.items():
            va = a.get(name)
            vb = b.get(name)
            if va is None or vb is None:
                continue
            if cfg["direction"] == "maximize":
                if va < vb:
                    at_least_as_good = False
                    break
                if va > vb:
                    strictly_better += 1
            else:  # minimize
                if va > vb:
                    at_least_as_good = False
                    break
                if va < vb:
                    strictly_better += 1
        return at_least_as_good and strictly_better > 0

    def pareto_route(self, task_type: str, task_content: str, constraints: dict = None) -> dict:
        """基于帕累托最优的多目标路由选择。

        从活跃路由策略中计算 success_rate、avg_duration_ms、load 等目标值，
        应用约束过滤器后生成非支配解集，并返回帕累托前沿。

        Args:
            task_type: 任务类型标识，用于匹配策略的 task_type_pattern。
            task_content: 任务内容文本，可用于基于关键字的约束过滤。
            constraints: 可选约束字典，支持 min_success_rate、max_duration_ms、max_load
                （以及任意与目标名称匹配的 min_<obj> / max_<obj> 约束）。

        Returns:
            dict: 包含以下键的字典：
                - pareto_front (list): 帕累托前沿（非支配解集），按权重综合得分降序排列。
                - non_dominated_solutions (list): 全部候选解，含支配状态标记。
                - total_strategies (int): 候选策略总数。
                - pareto_count (int): 帕累托前沿中的解数量。
                - filtered (bool): 约束过滤后是否无解（仅在过滤后为空时出现）。
                - objectives (dict): 使用的帕累托目标定义。
        """
        objectives = self._load_pareto_objectives()

        rows = self.db.execute("SELECT * FROM routing_strategies WHERE is_active=1 ORDER BY priority ASC").fetchall()

        strategies = []
        for row in rows:
            total = row["success_count"] + row["fail_count"]
            success_rate = row["success_count"] / total if total > 0 else 0.5
            strategies.append(
                {
                    "strategy_key": row["strategy_key"],
                    "strategy_name": row["name"],
                    "route_to": row["route_to"],
                    "success_rate": round(success_rate, 4),
                    "avg_duration_ms": row["avg_duration_ms"] or 0.0,
                    "load": total,
                    "priority": row["priority"],
                }
            )

        if not strategies:
            return {
                "pareto_front": [],
                "non_dominated_solutions": [],
                "total_strategies": 0,
                "pareto_count": 0,
                "objectives": objectives,
            }

        # apply constraints filter
        if constraints:
            filtered = list(strategies)
            for obj_name, cfg in objectives.items():
                constrain_key = f"min_{obj_name}"
                if constrain_key in constraints:
                    threshold = constraints[constrain_key]
                    if cfg["direction"] == "maximize":
                        filtered = [s for s in filtered if s.get(obj_name, 0) >= threshold]
                    else:
                        filtered = [s for s in filtered if s.get(obj_name, float("inf")) <= threshold]
                constrain_key = f"max_{obj_name}"
                if constrain_key in constraints:
                    threshold = constraints[constrain_key]
                    if cfg["direction"] == "maximize":
                        filtered = [s for s in filtered if s.get(obj_name, float("inf")) <= threshold]
                    else:
                        filtered = [s for s in filtered if s.get(obj_name, 0) >= threshold]
            if not filtered:
                return {
                    "pareto_front": [],
                    "non_dominated_solutions": [],
                    "total_strategies": len(strategies),
                    "pareto_count": 0,
                    "filtered": True,
                    "objectives": objectives,
                }
            strategies = filtered

        # generate non-dominated set (pareto front) with domination tracking
        non_dominated_solutions = []
        pareto_front = []
        for i, s in enumerate(strategies):
            dominated_by = []
            dominates_others = []
            for j, other in enumerate(strategies):
                if i == j:
                    continue
                if self._dominates(other, s, objectives):
                    dominated_by.append(j)
                if self._dominates(s, other, objectives):
                    dominates_others.append(j)
            is_dominated = len(dominated_by) > 0
            record = {
                **s,
                "dominated": is_dominated,
                "dominated_by_count": len(dominated_by),
                "dominates_count": len(dominates_others),
            }
            non_dominated_solutions.append(record)
            if not is_dominated:
                pareto_front.append(record)

        # rank within pareto front by weighted score (higher = better)
        for p in pareto_front:
            weighted_score = 0.0
            for name, cfg in objectives.items():
                raw = p.get(name, 0)
                w = cfg["weight"]
                weighted_score += w * raw if cfg["direction"] == "maximize" else w * (-raw)
            p["weighted_score"] = round(weighted_score, 4)

        pareto_front.sort(key=lambda x: (-x["weighted_score"], x["priority"]))

        return {
            "pareto_front": pareto_front,
            "non_dominated_solutions": non_dominated_solutions,
            "total_strategies": len(strategies),
            "pareto_count": len(pareto_front),
            "objectives": objectives,
        }
