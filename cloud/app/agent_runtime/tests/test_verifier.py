from unittest.mock import patch

from cloud.app.agent_runtime.models import CheckResult
from cloud.app.agent_runtime.verifier import Verifier


def test_verify_passes():
    """test verify passes."""
    v = Verifier()
    result = v.verify({"success": True, "result": "ok"})
    assert result in (True,)


def test_verify_completion_layer1_keyword_match():
    v = Verifier()
    conditions = ["Data imported successfully"]
    context = {
        "messages": [{"role": "user", "content": "工具返回：Data imported successfully, 100 rows"}],
        "last_tool_result": "Data imported successfully, 100 rows",
    }
    passed, reason = v.verify_completion(conditions, context)
    assert passed is True
    assert "Layer1 keyword match" in reason


def test_verify_completion_layer3_llm_fails():
    v = Verifier()
    conditions = ["All goals achieved"]
    context = {
        "messages": [{"role": "user", "content": "工具返回：only partial progress"}],
        "last_tool_result": "only partial progress",
    }
    with (
        patch.object(v, "_call_llm", return_value='{"passed": false, "reason": "conditions not met"}'),
        patch.object(v._guard, "check_params", return_value=CheckResult(name="param_boundary", passed=False, detail="Mocked fail")),
    ):
        passed, reason = v.verify_completion(conditions, context)
    assert passed is False
    assert "Layer3 LLM" in reason
