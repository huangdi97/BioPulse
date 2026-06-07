import json
import sqlite3
from pathlib import Path

import pytest

from cloud.app.agent_runtime.planner import Plan, PlanGenerator
from cloud.app.services.compliance_enforcer import ComplianceEnforcer

GOLDEN_DIR = Path(__file__).parent / "golden"


def _load_cases(filename: str) -> list[dict]:
    with open(GOLDEN_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def _memory_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return conn


def _case_ids(filename: str) -> list[str]:
    return [case["name"] for case in _load_cases(filename)]


def _assert_schema(value, schema: dict, path: str = "$") -> None:
    expected_type = schema.get("type")
    if expected_type:
        assert _matches_type(value, expected_type), f"{path}: expected type {expected_type}, got {type(value).__name__}"

    if expected_type == "object":
        required = schema.get("required", [])
        for field in required:
            assert field in value, f"{path}: missing required field {field}"
        for field, child_schema in schema.get("properties", {}).items():
            if field in value:
                _assert_schema(value[field], child_schema, f"{path}.{field}")

    if expected_type == "array":
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                _assert_schema(item, item_schema, f"{path}[{index}]")


def _matches_type(value, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "null":
        return value is None
    raise AssertionError(f"Unsupported schema type: {expected_type}")


@pytest.mark.parametrize("case", _load_cases("compliance_cases.json"), ids=_case_ids("compliance_cases.json"))
def test_compliance_golden(case):
    db = _memory_db()
    try:
        result = ComplianceEnforcer(db).check_visit(case["input"])
    finally:
        db.close()

    actual_action = "block" if result else "pass"
    expected_action = case["expected"]["action"]
    assert actual_action == expected_action, f"{case['name']}: expected action {expected_action}, got {actual_action}"

    actual_rule_names = [violation.rule_name for violation in result]
    expected_rule_names = case["expected"].get("rule_names", [])
    assert actual_rule_names == expected_rule_names, f"{case['name']}: expected rule_names {expected_rule_names}, got {actual_rule_names}"


@pytest.mark.parametrize("case", _load_cases("pipeline_cases.json"), ids=_case_ids("pipeline_cases.json"))
def test_pipeline_golden(case):
    plan = Plan(**case["plan"])
    assert PlanGenerator().validate_plan(plan), f"{case['name']}: plan failed validation"
    assert plan.goal == case["input"], f"{case['name']}: input goal and plan goal differ"

    actual_tools = {step.tool for step in plan.steps}
    expected_tools = set(case["expected_tools"])
    missing_tools = sorted(expected_tools - actual_tools)
    assert not missing_tools, f"{case['name']}: missing expected tools {missing_tools}"

    expected_count = case["expected_plan_count"]
    actual_count = len(plan.steps)
    assert expected_count["min"] <= actual_count <= expected_count["max"], (
        f"{case['name']}: expected plan count in {expected_count}, got {actual_count}"
    )


@pytest.mark.parametrize(
    "case",
    _load_cases("response_format_cases.json"),
    ids=_case_ids("response_format_cases.json"),
)
def test_response_format_golden(case):
    assert "sample_input" in case, f"{case['name']}: missing sample_input"
    _assert_schema(case["sample_output"], case["schema"])
