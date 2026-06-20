"""Tests for eval runner and reporter."""

import json

from cloud.app.eval.reporter import ci_exit, format_json, format_report
from cloud.app.eval.runner import EvalRunner


def test_load_cases_smoke():
    runner = EvalRunner(golden_cases_dir="golden_cases")
    cases = runner.load_cases("smoke")
    assert len(cases) == 7
    for c in cases:
        assert "smoke" in c.get("tags", [])


def test_load_cases_regression():
    runner = EvalRunner(golden_cases_dir="golden_cases")
    cases = runner.load_cases("regression")
    assert len(cases) == 7
    for c in cases:
        assert "regression" in c.get("tags", [])


def test_load_cases_all():
    runner = EvalRunner(golden_cases_dir="golden_cases")
    cases = runner.load_cases("all")
    assert len(cases) == 14


def test_load_cases_unknown_suite():
    runner = EvalRunner(golden_cases_dir="golden_cases")
    cases = runner.load_cases("nonexistent")
    assert len(cases) == 0


def test_dry_run():
    runner = EvalRunner(golden_cases_dir="golden_cases")
    cases = runner.load_cases("smoke")
    assert len(cases) > 0
    res = runner.run_case(cases[0])
    assert res["status"] == "dry_run"
    assert res["passed"] is None


def test_run_suite_dry():
    runner = EvalRunner(golden_cases_dir="golden_cases")
    report = runner.run_suite("smoke")
    assert report["total"] == 7
    assert report["passed"] == 0
    assert report["failed"] == 0
    assert len(report["results"]) == 7


def test_format_json():
    report = {"suite": "smoke", "total": 2, "passed": 1, "failed": 1, "results": []}
    output = format_json(report)
    parsed = json.loads(output)
    assert parsed["suite"] == "smoke"


def test_format_report():
    report = {"suite": "smoke", "total": 2, "passed": 1, "failed": 1, "results": []}
    output = format_report(report)
    assert "smoke" in output
    assert "Passed: 1" in output
    assert "Failed: 1" in output


def test_ci_exit_pass():
    report = {"total": 10, "passed": 10}
    assert ci_exit(report, 0.9) == 0


def test_ci_exit_fail():
    report = {"total": 10, "passed": 5}
    assert ci_exit(report, 0.9) == 1


def test_ci_exit_empty():
    report = {"total": 0, "passed": 0}
    assert ci_exit(report, 0.9) == 0
