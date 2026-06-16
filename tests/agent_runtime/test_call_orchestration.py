import pytest

from cloud.app.agent_runtime.runtime_llm.call_orchestration import process_ai_response


def test_process_ai_response_success():
    result = {
        "success": True,
        "data": {"data": {"reply": "Hello", "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}}},
        "model_tier": "cloud_normal",
        "attempts": 1,
        "cost": {},
    }
    output = process_ai_response(
        result=result, messages=[{"role": "user", "content": "hi"}], step=0, duration_s=0.5, tracer=None, trace_id="test", trace_data=[]
    )
    assert output["reply"] == "Hello"
    assert output["model_tier"] == "cloud_normal"


class StubTracer:
    def log_llm_call(self, tier, prompt_tokens, completion_tokens, duration_ms):
        self.last = {"tier": tier, "prompt": prompt_tokens, "completion": completion_tokens, "duration": duration_ms}


def test_process_ai_response_with_tracer():
    tracer = StubTracer()
    result = {
        "success": True,
        "data": {"data": {"reply": "OK", "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15}}},
        "model_tier": "local",
        "attempts": 2,
        "cost": {},
    }
    trace_data = []
    process_ai_response(result=result, messages=[], step=1, duration_s=0.3, tracer=tracer, trace_id="agent_x", trace_data=trace_data)
    assert tracer.last["tier"] == "local"
    assert len(trace_data) == 1


def test_process_ai_response_raises_on_failure():
    result = {"success": False, "attempts": 3, "error": "API timeout"}
    with pytest.raises(RuntimeError, match="API timeout"):
        process_ai_response(result=result, messages=[], step=0, duration_s=0.0, tracer=None, trace_id="x", trace_data=[])
