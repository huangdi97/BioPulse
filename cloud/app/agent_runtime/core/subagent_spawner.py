"""Subagent Spawner — 复杂任务自动拆解为子 Agent 并行执行，独立上下文窗口，通过 SharedState 聚合结果。"""

import logging
import threading
import uuid
from typing import Any

from cloud.app.agent_runtime.core.planner import Plan, Planner
from cloud.app.agent_runtime.core.shared_state import SharedStateEntry, get_shared_state

logger = logging.getLogger(__name__)


class SubagentSpawnError(Exception):
    """subagent spawn error."""


class SubagentSpawner:
    """分解复杂任务 → spawn 子 Agent → 收集结果 → 聚合。"""

    def __init__(self, planner: Planner | None = None):
        self._planner = planner or Planner()
        self._lock = threading.Lock()
        self._active: dict[str, list[str]] = {}

    def decompose_and_spawn(self, goal: str, tools: list[str] | None = None, max_subagents: int = 3) -> list[str]:
        """Planner 拆解目标 → 每个子任务 spawn 一个子 Agent → 返回 spawned_ids。"""
        plan = self._planner.generate_plan(goal, tools or [])
        if not plan.steps:
            raise SubagentSpawnError(f"Planner could not decompose goal: {goal}")

        batches = self._group_parallel_steps(plan)
        spawned_ids: list[str] = []
        for batch in batches[:max_subagents]:
            sub_goal = "; ".join(s.description for s in batch)
            sub_id = self.spawn(sub_goal, tools or [], "")
            spawned_ids.append(sub_id)
        return spawned_ids

    def spawn(self, goal: str, tools: list[str], parent_agent_key: str) -> str:
        """创建一个子 Agent 执行记录，写入 SharedState 子任务 namespace。"""
        sub_id = f"sub_{uuid.uuid4().hex[:12]}"
        namespace = f"subagent.{parent_agent_key}.{sub_id}" if parent_agent_key else f"subagent.anonymous.{sub_id}"

        entry = SharedStateEntry(
            namespace=namespace,
            key="spawn",
            value={
                "sub_id": sub_id,
                "goal": goal,
                "tools": tools,
                "status": "spawned",
                "parent_agent_key": parent_agent_key,
            },
            agent_key=parent_agent_key or "system",
        )
        get_shared_state().write(entry, caller_agent_key=parent_agent_key or "system")

        with self._lock:
            self._active.setdefault(parent_agent_key, []).append(sub_id)

        logger.info("Spawned subagent %s for goal: %s", sub_id, goal)
        return sub_id

    def collect_results(self, spawned_ids: list[str], timeout: float = 30.0) -> list[dict[str, Any]]:
        """等待子 Agent 完成，从 SharedState 收集结果。超时返回已收集部分。"""
        import time

        deadline = time.monotonic() + timeout
        results: list[dict[str, Any]] = []
        remaining = set(spawned_ids)

        while remaining and time.monotonic() < deadline:
            for sub_id in list(remaining):
                ss = get_shared_state()
                for prefix in ["subagent.", "subagent.anonymous."]:
                    ns = f"{prefix}{sub_id}"
                    entries = ss.read(namespace=ns, key="result")
                    for e in entries:
                        if isinstance(e.value, dict) and e.value.get("status") in ("completed", "failed"):
                            results.append(e.value)
                            remaining.discard(sub_id)
                            break
            if remaining:
                time.sleep(0.5)

        for sub_id in remaining:
            logger.warning("Subagent %s did not complete within timeout", sub_id)
            results.append({"sub_id": sub_id, "status": "timeout", "goal": "", "result": ""})

        return results

    def cancel_all(self, parent_agent_key: str) -> None:
        """取消父 Agent 的所有子 Agent — 写入取消信号到 SharedState。"""
        with self._lock:
            sub_ids = self._active.pop(parent_agent_key, [])

        for sub_id in sub_ids:
            namespace = f"subagent.{parent_agent_key}.{sub_id}"
            entry = SharedStateEntry(
                namespace=namespace,
                key="signal",
                value={"command": "cancel"},
                agent_key=parent_agent_key,
            )
            get_shared_state().write(entry, caller_agent_key=parent_agent_key)
            logger.info("Cancelled subagent %s", sub_id)

    @staticmethod
    def _group_parallel_steps(plan: Plan) -> list[list]:
        """将 PlanStep 按依赖关系分组可并行执行的批次。"""
        batches: list[list] = []
        assigned: set[str] = set()

        while len(assigned) < len(plan.steps):
            batch: list = []
            for s in plan.steps:
                if s.step_id in assigned:
                    continue
                if all(dep in assigned for dep in s.dependencies):
                    batch.append(s)
                    assigned.add(s.step_id)
            if not batch:
                assigned.update(s.step_id for s in plan.steps if s.step_id not in assigned)
                break
            batches.append(batch)

        return batches
