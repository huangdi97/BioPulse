"""回滚处理器 — Agent 执行失败时回退到任意历史步骤的重试机制。"""

import uuid

from fastapi import HTTPException


class RollbackHandler:
    def __init__(self, host):
        self._host = host

    def rollback(self, trace_id: str, target_step: int) -> dict:
        if target_step < 0:
            raise HTTPException(status_code=400, detail="step must be non-negative")
        state = self._host._load_runtime_snapshot(trace_id, target_step)
        if not state:
            raise HTTPException(status_code=404, detail="snapshot not found")
        agent_key, goal = state.get("agent_key"), state.get("goal")
        if not agent_key or not goal:
            raise HTTPException(status_code=400, detail="snapshot missing agent_key or goal")
        new_trace_id = self._host._trace_id = str(uuid.uuid4())
        self._host._trace_data = list(state.get("trace") or [])
        cost = state.get("cost") or {}
        self._host._cost_governor.restore_usage(cost)
        self._host._cost_tracker = {
            "prompt_tokens": cost.get("total_input_tokens", 0),
            "completion_tokens": cost.get("total_output_tokens", 0),
            "total_tokens": cost.get("total_tokens", 0),
            "total_cost": cost.get("total_cost", 0.0),
            "step_costs": cost.get("step_costs", []),
        }
        restored_state = {**state, "trace_id": new_trace_id, "step": target_step, "status": "rolled_back", "rolled_back_from": trace_id}
        self._host._save_checkpoint(agent_key, goal, restored_state)
        result = self._host.execute(goal, agent_key, restored_state.get("context"))
        new_trace_id = result.metadata.get("trace_id", self._host._trace_id)
        restored_state = {**state, "trace_id": new_trace_id, "step": target_step, "status": "rolled_back", "rolled_back_from": trace_id}
        self._host._save_checkpoint(agent_key, goal, restored_state)
        return {
            "trace_id": new_trace_id,
            "source_trace_id": trace_id,
            "agent_key": agent_key,
            "goal": goal,
            "step": target_step,
            "messages": restored_state.get("messages", []),
            "tool_calls_so_far": restored_state.get("tool_calls_so_far", 0),
            "cost": self._host.get_cost_usage(),
            "execution": result.model_dump(),
        }
