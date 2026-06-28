"""Agent evaluation runner — runs 50 test cases across 5 categories."""

import json


class EvalRunner:
    def __init__(self, cases_path: str = "cloud/app/tests/eval/eval_cases.json"):
        with open(cases_path) as f:
            raw = json.load(f)
        self.cases = raw["cases"]
        self.results = []

    def run(self, agent_fn) -> dict:
        self.results = []
        for case in self.cases:
            try:
                result = agent_fn(case["input"])
                passed = result.get("action") == case["expected"]["action"]
            except Exception:
                passed = False
            self.results.append({"id": case["id"], "category": case["category"], "passed": passed, "input": case["input"]})
        return self.summary()

    def summary(self) -> dict:
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        by_category = {}
        for r in self.results:
            by_category.setdefault(r["category"], {"total": 0, "passed": 0})
            by_category[r["category"]]["total"] += 1
            if r["passed"]:
                by_category[r["category"]]["passed"] += 1
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round(passed / total * 100, 1) if total else 0.0,
            "by_category": by_category,
        }


def _dummy_agent(input_str: str):
    mapping = {
        "回扣": {"action": "reject"},
        "患者信息": {"action": "block"},
        "off-label": {"action": "reject"},
        "未成年人": {"action": "reject"},
        "样品": {"action": "flag"},
        "诋毁": {"action": "reject"},
        "赞助合规": {"action": "allow"},
        "旅游": {"action": "reject"},
        "不完整": {"action": "flag"},
        "数据引用": {"action": "allow"},
        "频率超标": {"action": "flag"},
        "无预约": {"action": "flag"},
        "缺失": {"action": "flag"},
        "合规拜访": {"action": "allow"},
        "授权区域": {"action": "reject"},
        "非工作时间": {"action": "flag"},
        "团队陪同": {"action": "allow"},
        "时长超限": {"action": "flag"},
        "合规材料": {"action": "flag"},
        "签名齐全": {"action": "allow"},
        "商业机密": {"action": "reject"},
        "公开信息": {"action": "allow"},
        "冒充": {"action": "reject"},
        "价格调研": {"action": "allow"},
        "数据对比": {"action": "allow"},
        "询问机密": {"action": "reject"},
        "展会": {"action": "allow"},
        "逆向工程": {"action": "reject"},
        "学术文献": {"action": "allow"},
        "跟踪": {"action": "reject"},
        "超标": {"action": "flag"},
        "虚构": {"action": "reject"},
        "差旅报销": {"action": "allow"},
        "重复提交": {"action": "reject"},
        "油费": {"action": "allow"},
        "无票据": {"action": "flag"},
        "超预算": {"action": "flag"},
        "礼品": {"action": "flag"},
        "培训费用": {"action": "allow"},
        "分摊": {"action": "flag"},
    }
    for keyword, result in mapping.items():
        if keyword in input_str:
            return result
    return {"action": "analyze"}


def test_eval_runner_loads_cases():
    runner = EvalRunner()
    assert len(runner.cases) == 50


def test_eval_runner_all_categories():
    runner = EvalRunner()
    cats = set(c["category"] for c in runner.cases)
    assert cats == {"compliance", "visit", "competitor", "expense", "analysis"}


def test_eval_runner_summary():
    runner = EvalRunner()
    summary = runner.run(_dummy_agent)
    assert summary["total"] == 50
    assert summary["passed"] + summary["failed"] == 50
    assert 0 <= summary["pass_rate"] <= 100


def test_eval_runner_by_category():
    runner = EvalRunner()
    summary = runner.run(_dummy_agent)
    assert len(summary["by_category"]) == 5
    for cat, stats in summary["by_category"].items():
        assert stats["total"] == 10
        assert 0 <= stats["passed"] <= 10
