"""Agent 流水线模块，按拓扑序执行多步骤工具调用链。"""

import json

from pydantic import BaseModel

from cloud.app.agent_runtime.tool_bridge import ToolBridge
from shared.config import settings as config_settings


class PipelineStep(BaseModel):
    """流水线步骤定义，含工具名、参数模板、依赖关系及输出键。"""

    step_id: str
    tool: str
    params_template: dict
    depends_on: list[str] = []
    output_key: str


class Pipeline:
    """Agent 流水线执行器，按依赖拓扑排序解析参数并依次调用工具。"""

    def __init__(self, steps: list[PipelineStep], tool_registry: ToolBridge, llm_func=None):
        self._steps = steps
        self._step_map = {s.step_id: s for s in steps}
        self._tool_registry = tool_registry
        self._llm_func = llm_func or self._default_llm

    def _default_llm(self, messages: list[dict]) -> str:
        import urllib.request

        body = json.dumps({"messages": messages, "temperature": 0.3, "max_tokens": 1024}).encode("utf-8")
        req = urllib.request.Request(
            f"{config_settings.ai_chat_url}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as rp:
            data = json.loads(rp.read().decode("utf-8"))
        return data.get("data", {}).get("reply", "")

    def _resolve_params(self, step: PipelineStep, run_context: dict) -> dict:
        prompt = (
            f"基于当前上下文，为工具「{step.tool}」填充参数。\n"
            f"参数模板：{json.dumps(step.params_template, ensure_ascii=False)}\n"
            f"当前上下文：{json.dumps(run_context, ensure_ascii=False)}\n\n"
            f"请直接返回 JSON 对象，键与参数模板一致，值为填充后的实际参数。"
        )
        reply = self._llm_func([{"role": "user", "content": prompt}])
        reply = reply.strip()
        if reply.startswith("```"):
            reply = reply.split("\n", 1)[-1]
            reply = reply.rsplit("```", 1)[0]
        return json.loads(reply)

    def _topological_order(self) -> list[PipelineStep]:
        sorted_steps = []
        visited = set()

        def dfs(step_id):
            if step_id in visited:
                return
            visited.add(step_id)
            step = self._step_map.get(step_id)
            if step is None:
                return
            for dep in step.depends_on:
                dfs(dep)
            sorted_steps.append(step)

        for step in self._steps:
            dfs(step.step_id)
        return sorted_steps

    def execute(self, context: dict, auth_header: str = "") -> dict:
        outputs = {}
        run_ctx = dict(context)

        for step in self._topological_order():
            for dep in step.depends_on:
                if dep in outputs:
                    run_ctx[outputs[dep]["output_key"]] = outputs[dep]["result"]

            params = self._resolve_params(step, run_ctx)
            result = self._tool_registry.call(step.tool, params, auth_header)

            outputs[step.step_id] = {
                "step_id": step.step_id,
                "tool": step.tool,
                "params": params,
                "result": result,
                "output_key": step.output_key,
            }
            run_ctx[step.output_key] = result

        return outputs


AgentPipeline = Pipeline
