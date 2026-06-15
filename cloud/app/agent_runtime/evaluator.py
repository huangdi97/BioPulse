"""Agent 输出质量评估框架 — 支持基本评估指标与结果存储。"""

import json
import logging
import random

from cloud.app.agent_runtime.content_filter import check_output

logger = logging.getLogger(__name__)

EVAL_SAMPLE_RATE = 0.01


def is_json(text: str) -> bool:
    """检查字符串是否为合法 JSON。"""
    try:
        json.loads(text)
        return True
    except (ValueError, TypeError):
        return False


def contains_harmful(text: str) -> bool:
    """检查文本是否包含有害内容。"""
    return check_output(text) is not None


class AgentEvaluator:
    """Agent 输出质量评估框架。

    支持指标：
        - exact_match: 输出精确匹配期望值
        - contains: 输出包含期望子串
        - json_valid: 输出是合法 JSON
        - no_harm: 输出不包含有害内容

    支持 auto_eval 模式：可配置采样率、实时评估、趋势看板。
    """

    EVAL_METRICS = {
        "exact_match": lambda output, expected: output.strip() == expected.strip() if expected else True,
        "contains": lambda output, expected: (expected or "") in output,
        "json_valid": lambda output, _: is_json(output),
        "no_harm": lambda output, _: not contains_harmful(output),
    }

    def __init__(self, db=None, sample_rate: float = 0.01, auto_eval: bool = False):
        self._db = db
        self._sample_rate = sample_rate
        self._auto_eval = auto_eval
        self._ensure_table()

    @property
    def sample_rate(self) -> float:
        """获取评估采样率。"""
        return self._sample_rate

    @sample_rate.setter
    def sample_rate(self, rate: float):
        """设置评估采样率。"""
        self._sample_rate = max(0.0, min(1.0, rate))

    @property
    def auto_eval(self) -> bool:
        """获取自动评估模式状态。"""
        return self._auto_eval

    @auto_eval.setter
    def auto_eval(self, enabled: bool):
        """启用或禁用自动评估模式。"""
        self._auto_eval = enabled

    def _ensure_table(self):
        if not self._db:
            return
        try:
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS agent_eval_results ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "agent_name TEXT NOT NULL, "
                "trace_id TEXT DEFAULT '', "
                "input_data TEXT DEFAULT '{}', "
                "output_data TEXT DEFAULT '{}', "
                "expected_data TEXT DEFAULT '{}', "
                "metrics_json TEXT DEFAULT '{}', "
                "passed INTEGER DEFAULT 0, "
                "score REAL DEFAULT 0.0, "
                "created_at TEXT DEFAULT (datetime('now'))"
                ")"
            )
            self._db.commit()
        except Exception:
            logger.exception("Failed to create eval_results table")

    def evaluate(self, agent_name: str, input_data: dict, output_data: dict, expected: dict | None = None, trace_id: str = "") -> dict:
        """评估 Agent 输出质量。"""
        if not self._auto_eval and not self.should_sample():
            return {"sampled": False, "score": 0.0, "passed": False}
        results = {}
        for metric_name, metric_fn in self.EVAL_METRICS.items():
            metric_expected = expected.get(metric_name) if expected else None
            try:
                passed = metric_fn(output_data.get("result", ""), metric_expected)
            except Exception:
                logger.warning("Evaluator metric exception", exc_info=True)
                passed = False
            results[metric_name] = passed
        passed_all = all(results.values())
        score = sum(1 for v in results.values() if v) / max(len(results), 1)
        eval_result = {
            "agent_name": agent_name,
            "trace_id": trace_id,
            "input_data": input_data,
            "output_data": output_data,
            "expected": expected or {},
            "metrics": results,
            "passed": passed_all,
            "score": score,
        }
        self._save(eval_result)
        return eval_result

    def _save(self, result: dict) -> None:
        if not self._db:
            return
        try:
            self._db.execute(
                "INSERT INTO agent_eval_results (agent_name, trace_id, input_data, output_data, expected_data, metrics_json, passed, score) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    result["agent_name"],
                    result["trace_id"],
                    json.dumps(result["input_data"], ensure_ascii=False),
                    json.dumps(result["output_data"], ensure_ascii=False),
                    json.dumps(result["expected"], ensure_ascii=False),
                    json.dumps(result["metrics"], ensure_ascii=False),
                    1 if result["passed"] else 0,
                    result["score"],
                ),
            )
            self._db.commit()
        except Exception:
            logger.exception("Failed to save eval result")

    def get_dashboard(self) -> dict:
        """获取所有 Agent 的评估看板数据。"""
        if not self._db:
            return {"agents": []}
        rows = self._db.execute(
            "SELECT agent_name, "
            "ROUND(AVG(score), 4) as avg_score, "
            "COUNT(*) as total_evals, "
            "SUM(CASE WHEN passed=1 THEN 1 ELSE 0 END) as passed_count, "
            "MIN(created_at) as first_eval, "
            "MAX(created_at) as last_eval "
            "FROM agent_eval_results "
            "GROUP BY agent_name "
            "ORDER BY last_eval DESC"
        ).fetchall()
        agents = []
        for r in rows:
            agent_name = r["agent_name"]
            trend_rows = self._db.execute(
                "SELECT score, created_at FROM agent_eval_results WHERE agent_name=? ORDER BY created_at DESC LIMIT 20",
                (agent_name,),
            ).fetchall()
            scores = [tr["score"] for tr in reversed(trend_rows)]
            agents.append(
                {
                    "agent_name": agent_name,
                    "avg_score": r["avg_score"],
                    "total_evals": r["total_evals"],
                    "passed_count": r["passed_count"],
                    "pass_rate": round(r["passed_count"] / max(r["total_evals"], 1) * 100, 2),
                    "first_eval": r["first_eval"],
                    "last_eval": r["last_eval"],
                    "recent_scores": scores,
                }
            )
        return {"agents": agents}

    def should_sample(self) -> bool:
        """判断当前是否应采样评估。"""
        return random.random() < self._sample_rate
