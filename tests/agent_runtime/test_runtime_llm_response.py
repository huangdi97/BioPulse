from cloud.app.agent_runtime.runtime_llm.response import usage_from_route_result


def test_usage_from_failed_result():
    assert usage_from_route_result({"success": False}) == {}


def test_usage_from_success_result():
    result = {"success": True, "data": {"data": {"usage": {"prompt_tokens": 10}}}}
    usage = usage_from_route_result(result)
    assert usage["prompt_tokens"] == 10


def test_usage_no_usage_key():
    result = {"success": True, "data": {"data": {}}}
    assert usage_from_route_result(result) == {}
