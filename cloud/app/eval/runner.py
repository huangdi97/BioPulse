"""EvalRunner — 黄金用例加载与执行核心。"""

import glob
import json
import os


class EvalRunner:
    def __init__(self, golden_cases_dir: str = "golden_cases"):
        self._golden_cases_dir = golden_cases_dir

    def load_cases(self, suite: str) -> list[dict]:
        cases = []
        pattern = os.path.join(self._golden_cases_dir, "*", "*.json")
        for filepath in sorted(glob.glob(pattern)):
            with open(filepath) as f:
                case = json.load(f)
            tags = case.get("tags", [])
            if suite in tags or suite == "all":
                case["_filepath"] = filepath
                cases.append(case)
        return cases

    def run_case(self, case: dict, runtime_core=None) -> dict:
        if runtime_core is None:
            return self._dry_run(case)
        result = runtime_core.execute(
            goal=case["goal"],
            agent_key=case["agent_key"],
            context=case.get("input_context"),
        )
        return self._check_result(case, result)

    def run_suite(self, suite: str, runtime_core=None) -> dict:
        cases = self.load_cases(suite)
        results = []
        passed = 0
        failed = 0
        for case in cases:
            res = self.run_case(case, runtime_core)
            results.append(res)
            if res.get("passed") is True:
                passed += 1
            elif res.get("passed") is False:
                failed += 1
        return {
            "suite": suite,
            "total": len(cases),
            "passed": passed,
            "failed": failed,
            "results": results,
        }

    def _dry_run(self, case: dict) -> dict:
        expected = case.get("expected", {})
        return {
            "agent_key": case["agent_key"],
            "goal": case["goal"],
            "tags": case.get("tags", []),
            "passed": None,
            "status": "dry_run",
            "expected": expected,
        }

    def _check_result(self, case: dict, result) -> dict:
        expected = case.get("expected", {})
        exp_status = expected.get("status", "success")
        status_ok = result.status == exp_status
        output = result.result or ""
        contains_ok = all(phrase in output for phrase in expected.get("output_contains", []))
        not_contains_ok = all(phrase not in output for phrase in expected.get("output_not_contains", []))
        passed = status_ok and contains_ok and not_contains_ok
        return {
            "agent_key": case["agent_key"],
            "goal": case["goal"],
            "tags": case.get("tags", []),
            "passed": passed,
            "status": result.status,
            "expected": expected,
            "actual_output": output[:500],
        }
