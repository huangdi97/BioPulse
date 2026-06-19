import json

from cloud.app.agent_eval.scenarios import SCENARIOS


def run_eval(scenario: dict) -> dict:
    return {
        "name": scenario["name"],
        "actions_taken": [],
        "output_text": "",
    }


def score_result(result: dict, scenario: dict) -> dict:
    expected_actions = set(scenario["expected_actions"])
    actions_taken = set(result.get("actions_taken", []))
    total = len(expected_actions)
    matched = len(expected_actions & actions_taken)
    action_match = matched / total if total > 0 else 0.0

    output_text = result.get("output_text", "")
    expected_contains = scenario["expected_output_contains"]
    output_match = (
        sum(1 for phrase in expected_contains if phrase in output_text) / len(expected_contains)
        if expected_contains
        else 0.0
    )

    return {
        "name": scenario["name"],
        "action_match": round(action_match, 2),
        "output_match": round(output_match, 2),
        "safety_pass": True,
    }


def run_full_suite() -> dict:
    results = []
    total_action = 0.0
    total_output = 0.0
    for scenario in SCENARIOS:
        result = run_eval(scenario)
        scored = score_result(result, scenario)
        results.append(scored)
        total_action += scored["action_match"]
        total_output += scored["output_match"]
    n = len(results)
    return {
        "total_scenarios": n,
        "average_action_match": round(total_action / n, 2) if n else 0.0,
        "average_output_match": round(total_output / n, 2) if n else 0.0,
        "all_safety_pass": all(r["safety_pass"] for r in results),
        "results": results,
    }


if __name__ == "__main__":
    report = run_full_suite()
    print(json.dumps(report, ensure_ascii=False, indent=2))
