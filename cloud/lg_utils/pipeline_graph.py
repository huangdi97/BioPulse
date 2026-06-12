"""LangGraph 多步骤流水线图：按步骤顺序调用 AI 接口并聚合输出。"""

import json
import urllib.request
from typing import Optional, TypedDict

from langgraph.graph import END, StateGraph

from shared.ai_gateway import LLM_INFERENCE_TIMEOUT
from shared.app_settings import settings


class PipelineState(TypedDict):
    """流水线执行状态：步骤列表、当前索引、累积输出等。"""

    steps: list
    current_index: int
    accumulated_outputs: list
    current_step_input: Optional[dict]
    done: bool
    auth_header: str
    previous_output: str
    user_input: str


def step_executor(state: PipelineState) -> dict:
    steps = state["steps"]
    idx = state["current_index"]
    if idx >= len(steps):
        return {"done": True}

    step = steps[idx]
    auth_header = state.get("auth_header", "")
    previous_output = state.get("previous_output", "")
    user_input = state.get("user_input", "")

    input_mapping = step.get("input_mapping", {})
    user_content = user_input
    if input_mapping.get("user_input") == "$request":
        user_content = user_input
    ctx = input_mapping.get("context", "")
    strategy = input_mapping.get("strategy", "")
    if previous_output:
        if ctx == "previous_output" or strategy == "previous_output":
            user_content = previous_output
        if not input_mapping:
            user_content = previous_output

    system_prompt = step.get("custom_prompt_override") or step.get("system_prompt", "")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    payload = {
        "messages": messages,
        "temperature": step.get("temperature", 0.7),
        "max_tokens": step.get("max_tokens", 2048),
    }

    try:
        req = urllib.request.Request(
            f"{settings.cloud_api_base}/ai/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": auth_header},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=LLM_INFERENCE_TIMEOUT) as rp:
            resp = json.loads(rp.read().decode("utf-8"))
            ai_raw = resp.get("data", {}).get("reply", "")
            usage = resp.get("data", {}).get("usage", {})
            tokens = usage.get("total_tokens", 0) if usage else 0
            output_data = ai_raw
            status = "completed"
    except Exception as e:
        output_data = str(e)
        tokens = 0
        status = "failed"

    new_outputs = state["accumulated_outputs"] + [
        {
            "step_order": step.get("step_order", idx),
            "agent_name": step.get("agent_name", ""),
            "output": output_data,
            "status": status,
            "tokens": tokens,
            "messages": messages,
        }
    ]

    return {
        "current_index": idx + 1,
        "accumulated_outputs": new_outputs,
        "previous_output": output_data,
        "done": status == "failed" or idx + 1 >= len(steps),
    }


def should_continue(state: PipelineState) -> str:
    if state.get("done", False):
        return "done"
    return "continue"


def get_pipeline_graph():
    builder = (
        StateGraph(PipelineState)
        .add_node("step_executor", step_executor)
        .add_conditional_edges(
            "step_executor",
            should_continue,
            {
                "continue": "step_executor",
                "done": END,
            },
        )
        .set_entry_point("step_executor")
    )
    return builder.compile()
