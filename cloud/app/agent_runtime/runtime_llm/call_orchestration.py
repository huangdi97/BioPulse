"""Response processing and orchestration for LLM calls."""

import json
from datetime import datetime

from cloud.app.agent_runtime.metrics import agent_llm_duration, agent_tokens_total


def process_ai_response(result, messages, step, duration_s, tracer, trace_id, trace_data):
    if result["success"]:
        prompt_text = json.dumps(messages, ensure_ascii=False)
        input_len = len(prompt_text)
        ai_response = result["data"]
        data = ai_response.get("data", {})
        raw_response = json.dumps(ai_response, ensure_ascii=False)
        output_len = len(raw_response)

        if tracer:
            tier = result.get("model_tier", "cloud_normal")
            usage = data.get("usage", {})
            tracer.log_llm_call(
                tier,
                int(usage.get("prompt_tokens", 0) or 0),
                int(usage.get("completion_tokens", 0) or 0),
                int(duration_s * 1000),
            )

        trace_data.append(
            {
                "step": step,
                "input_len": input_len,
                "output_len": output_len,
                "duration_s": duration_s,
                "timestamp": datetime.now().isoformat(),
            }
        )

        model_tier = result.get("model_tier", "cloud_normal")
        agent_llm_duration.labels(agent_name=trace_id, model=model_tier).observe(duration_s)
        usage = data.get("usage", {})
        total_tokens = int(usage.get("total_tokens", 0) or 0)
        if total_tokens:
            agent_tokens_total.labels(agent_name=trace_id).inc(total_tokens)
        return {
            "reply": data.get("reply", ""),
            "usage": usage,
            "prompt": prompt_text,
            "raw_response": raw_response,
            "retry_count": result["attempts"] - 1,
            "cost": result.get("cost", {}),
            "model_tier": model_tier,
        }
    raise RuntimeError(f"LLM call failed after {result['attempts']} attempts: {result['error']}")
