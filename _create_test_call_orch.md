Write the file tests/agent_runtime/test_call_orchestration.py with this exact Python code:

```python
"""Tests for call_orchestration module."""

import pytest
from cloud.app.agent_runtime.runtime_llm.call_orchestration import process_ai_response


class StubTracer:
    def log_llm_call(self, tier, prompt_tokens, completion_tokens, duration_ms):
        self.last = {"tier": tier, "prompt": prompt_tokens, "completion": completion_tokens, "duration": duration_ms}


def test_process_ai_response_success():
    """process_ai_response should return processed result dict on success."""
    result = {
        "success": True,
        "data": {
            "data": {
                "reply": "Hello",
                "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            }
        },
        "model_tier": "cloud_normal",
        "attempts": 1,
        "cost": {"total": 0.01},
    }
    output = process_ai_response(
        result=result,
        messages=[{"role": "user", "content": "hi"}],
        step=0,
        duration_s=0.5,
        tracer=None,
        trace_id="test_agent",
        trace_data=[],
    )
    assert output["reply"] == "Hello"
    assert output["model_tier"] == "cloud_normal"
    assert output["retry_count"] == 0
    assert output["usage"]["total_tokens"] == 30


def test_process_ai_response_with_tracer():
    """process_ai_response should call tracer.log_llm_call when tracer is provided."""
    tracer = StubTracer()
    result = {
        "success": True,
        "data": {
            "data": {
                "reply": "OK",
                "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
            }
        },
        "model_tier": "local",
        "attempts": 2,
        "cost": {},
    }
    trace_data = []
    process_ai_response(
        result=result, messages=[], step=1, duration_s=0.3, tracer=tracer, trace_id="agent_x", trace_data=trace_data,
    )
    assert tracer.last["tier"] == "local"
    assert tracer.last["prompt"] == 5
    assert len(trace_data) == 1
    assert trace_data[0]["step"] == 1


def test_process_ai_response_raises_on_failure():
    """process_ai_response should raise RuntimeError when result is not successful."""
    result = {"success": False, "attempts": 3, "error": "API timeout"}
    with pytest.raises(RuntimeError, match="API timeout"):
        process_ai_response(
            result=result, messages=[], step=0, duration_s=0.0, tracer=None, trace_id="x", trace_data=[],
        )
```

Then run: python -m py_compile tests/agent_runtime/test_call_orchestration.py
