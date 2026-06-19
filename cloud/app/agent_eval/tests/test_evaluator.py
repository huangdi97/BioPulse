from cloud.app.agent_eval.evaluator import run_full_suite, score_result


def test_score_result_perfect_match():
    scenario = {
        "name": "test",
        "input": "",
        "expected_actions": ["check_compliance", "query_regulations"],
        "expected_output_contains": ["合规", "推广"],
        "risk_level": "high",
    }
    result = {"actions_taken": ["check_compliance", "query_regulations"], "output_text": "本次推广符合合规要求"}
    scored = score_result(result, scenario)
    assert scored["action_match"] == 1.0
    assert scored["output_match"] == 1.0
    assert scored["safety_pass"] is True


def test_score_result_partial_match():
    scenario = {
        "name": "test",
        "input": "",
        "expected_actions": ["check_compliance", "query_regulations", "query_kpi"],
        "expected_output_contains": ["合规", "推广", "建议"],
        "risk_level": "high",
    }
    result = {"actions_taken": ["check_compliance"], "output_text": "合规"}
    scored = score_result(result, scenario)
    assert scored["action_match"] == 1 / 3
    assert scored["output_match"] == 1 / 3


def test_score_result_no_match():
    scenario = {
        "name": "test",
        "input": "",
        "expected_actions": ["check_compliance"],
        "expected_output_contains": ["合规"],
        "risk_level": "high",
    }
    result = {"actions_taken": [], "output_text": ""}
    scored = score_result(result, scenario)
    assert scored["action_match"] == 0.0
    assert scored["output_match"] == 0.0


def test_score_result_empty_expected():
    scenario = {
        "name": "test",
        "input": "",
        "expected_actions": [],
        "expected_output_contains": [],
        "risk_level": "low",
    }
    result = {"actions_taken": [], "output_text": ""}
    scored = score_result(result, scenario)
    assert scored["action_match"] == 0.0
    assert scored["output_match"] == 0.0


def test_full_suite_ten_scenarios():
    report = run_full_suite()
    assert report["total_scenarios"] == 10
    assert report["all_safety_pass"] is True
    assert 0.0 <= report["average_action_match"] <= 1.0
    assert 0.0 <= report["average_output_match"] <= 1.0
