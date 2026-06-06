"""Agent 运行时核心，编排 LLM 推理、工具调用、循环检测与状态持久化。"""

import json
import time
import urllib.request
import uuid
from datetime import datetime
from functools import partial

from cloud.app.agent_runtime.agent_specs import AGENT_SPECS
from cloud.app.agent_runtime.cost_governor import CostGovernor
from cloud.app.agent_runtime.guard import sanitize_tool_output
from cloud.app.agent_runtime.loop_detector import LoopDetector
from cloud.app.agent_runtime.memory import AgentBrain
from cloud.app.agent_runtime.models import RuntimeResult
from cloud.app.agent_runtime.notifier import AgentNotifier
from cloud.app.agent_runtime.planner import PlanGenerator
from cloud.app.agent_runtime.retry import retry_with_backoff
from cloud.app.agent_runtime.runtime_state import ApprovalManager, CheckpointManager
from cloud.app.agent_runtime.state_snapshot import SnapshotManager
from cloud.app.agent_runtime.tool_bridge import ToolRegistry
from cloud.app.agent_runtime.validator import AgentOutputValidator
from cloud.app.agent_runtime.verifier import Verifier


class AgentRuntime:
    """Agent 运行时主控制器，管理 LLM 对话循环、工具调用、检查点与审批流程。"""

    def __init__(self, agent_db, business_db, auth_header: str, notifier: AgentNotifier | None = None):
        self._agent_db = agent_db
        self._db = business_db
        self._auth_header = auth_header
        self._notifier = notifier
        self._tool_registry = ToolRegistry()
        self._tool_registry.register_default_tools()
        self._brain = AgentBrain(agent_db)
        self._tool_registry.set_brain(self._brain)
        self._stats = {"total_runs": 0, "success_count": 0, "fail_count": 0}
        self._trace_id = str(uuid.uuid4())
        self._cost_tracker = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self._loop_detector = LoopDetector()
        self._checkpoint = CheckpointManager(agent_db)
        self._approval = ApprovalManager(agent_db)
        self._snapshot_manager = SnapshotManager(agent_db)
        self._cost_governor = CostGovernor()
        self._planner = PlanGenerator()
        self._verifier = Verifier()
        self._trace_data: list[dict] = []

    def execute(self, goal: str, agent_key: str, context: dict | None = None) -> RuntimeResult:
        try:
            return self._execute_impl(goal, agent_key, context)
        except Exception:
            self._save_snapshot(agent_key, -1, [], [], context or {}, "failed")
            raise

    def _execute_impl(self, goal: str, agent_key: str, context: dict | None = None) -> RuntimeResult:
        spec = AGENT_SPECS.get(agent_key)
        if spec is None:
            return RuntimeResult(
                status="error",
                result=f"unknown agent_key: {agent_key}",
                iterations=0,
                tool_calls=0,
                logs=[],
            )

        logs = []
        tool_calls = 0
        max_iter = min(spec["max_iterations"], 15)
        started_at = datetime.now().isoformat()

        checkpoint = self._checkpoint.load(agent_key, goal)
        if checkpoint:
            messages = checkpoint["messages"]
            logs = checkpoint["logs"]
            tool_calls = checkpoint["tool_calls_so_far"]
            start_step = checkpoint["step"] + 1
        else:
            system_prompt = (
                f"你是一个{spec['role_desc']}\n\n"
                f"可用工具（JSON格式）：{json.dumps(self._tool_registry.list_tools(), ensure_ascii=False)}\n\n"
                f"当前上下文：{json.dumps(context or {}, ensure_ascii=False)}\n\n"
                '请回复JSON格式：{"action": "call_tool"|"complete"|"error", "tool": "tool_name", "params": {...}, "reasoning": "..."}'
            )
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": goal},
            ]
            start_step = 0

        # 检查是否有已批准的审批（resume 流程）
        approved_tool = None
        approved_tool_params = None
        if checkpoint:
            app = self._agent_db.execute(
                "SELECT tool, params FROM agent_runtime_approvals WHERE agent_key=? AND goal=? AND status='approved' ORDER BY id DESC LIMIT 1",
                (agent_key, goal),
            ).fetchone()
            if app:
                approved_tool = app["tool"]
                approved_tool_params = json.loads(app["params"]) if app["params"] else {}

        plan = self._planner.plan(goal, agent_key, context)
        logs.append(plan)

        for step in range(start_step, max_iter):
            messages = self._compress_messages(messages)
            step_start = time.time()

            # 如果有已批准的审批，直接执行该工具（跳过 LLM 思考）
            if approved_tool and step == start_step:
                tool_result = self._tool_registry.call(approved_tool, approved_tool_params, self._auth_header, caller_permission="write")
                self._verifier.verify(tool_result)
                if tool_result.get("needs_approval"):
                    tool_result = {"success": False, "data": None, "error": "still requires approval"}
                tool_calls += 1
                tool_output_text = json.dumps(tool_result, ensure_ascii=False)
                safe_output = sanitize_tool_output(tool_output_text)
                duration_ms = int((time.time() - step_start) * 1000)
                logs.append(
                    {
                        "step": step,
                        "action": "call_tool",
                        "tool": approved_tool,
                        "params": approved_tool_params,
                        "result": safe_output,
                        "duration_ms": duration_ms,
                        "llm_prompt": None,
                        "llm_raw_response": None,
                        "llm_token_usage": None,
                        "tool_input": json.dumps(approved_tool_params, ensure_ascii=False),
                        "tool_output": tool_output_text,
                        "retry_count": 0,
                        "trace_id": self._trace_id,
                    }
                )
                self._checkpoint.save(
                    agent_key,
                    goal,
                    {
                        "trace_id": self._trace_id,
                        "step": step,
                        "messages": messages,
                        "logs": logs,
                        "tool_calls_so_far": tool_calls,
                        "goal": goal,
                        "agent_key": agent_key,
                        "context": context,
                        "trace": self._trace_data,
                    },
                    self._trace_id,
                )
                messages.append(
                    {
                        "role": "assistant",
                        "content": json.dumps({"action": "call_tool", "tool": approved_tool, "params": approved_tool_params}, ensure_ascii=False),
                    }
                )
                messages.append({"role": "user", "content": f"工具返回：{safe_output}"})
                approved_tool = None
                self._save_snapshot(agent_key, step, messages, logs, context)
                continue  # 跳过 LLM 解析，直接下一轮
            else:
                estimated_input = self._estimate_token_count(messages)
                estimated_output = 2048
                if not self._cost_governor.check("deepseek-chat", estimated_input, estimated_output):
                    logs.append(
                        {
                            "step": step,
                            "action": "budget_exceeded",
                            "tool": None,
                            "params": None,
                            "result": "cost budget exceeded",
                            "duration_ms": int((time.time() - step_start) * 1000),
                            "trace_id": self._trace_id,
                        }
                    )
                    continue
                try:
                    ai_resp = self._call_ai(messages, spec["default_temperature"], step)
                    usage = ai_resp.get("usage", {})
                    self._cost_tracker["prompt_tokens"] += usage.get("prompt_tokens", 0)
                    self._cost_tracker["completion_tokens"] += usage.get("completion_tokens", 0)
                    self._cost_tracker["total_tokens"] += usage.get("total_tokens", 0)
                    self._cost_governor.record("deepseek-chat", usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
                except Exception as e:
                    logs.append(
                        {
                            "step": step,
                            "action": "error",
                            "tool": None,
                            "params": None,
                            "result": str(e),
                            "duration_ms": int((time.time() - step_start) * 1000),
                            "llm_prompt": None,
                            "llm_raw_response": None,
                            "llm_token_usage": None,
                            "tool_input": None,
                            "tool_output": None,
                            "retry_count": 0,
                            "trace_id": self._trace_id,
                        }
                    )
                    self._save_snapshot(agent_key, step, messages, logs, context, "failed")
                    rolled_back = self._try_rollback(agent_key)
                    if rolled_back:
                        messages, logs, context = rolled_back
                        continue
                    raise

            duration_ms = int((time.time() - step_start) * 1000)
            reply = ai_resp["reply"]

            decision, validation_error = AgentOutputValidator.validate(reply)
            if validation_error or decision is None:
                logs.append(
                    {
                        "step": step,
                        "action": "error",
                        "tool": None,
                        "params": None,
                        "result": validation_error or "invalid decision",
                        "duration_ms": duration_ms,
                        "llm_prompt": ai_resp.get("prompt"),
                        "llm_raw_response": ai_resp.get("raw_response"),
                        "llm_token_usage": ai_resp.get("usage"),
                        "tool_input": None,
                        "tool_output": None,
                        "retry_count": ai_resp.get("retry_count", 0),
                        "trace_id": self._trace_id,
                    }
                )
                continue

            action = decision.action
            tool_name = decision.tool
            tool_params = decision.params or {}

            if action == "complete":
                logs.append(
                    {
                        "step": step,
                        "action": "complete",
                        "tool": None,
                        "params": None,
                        "result": decision.get("reasoning", ""),
                        "duration_ms": duration_ms,
                        "llm_prompt": ai_resp.get("prompt"),
                        "llm_raw_response": ai_resp.get("raw_response"),
                        "llm_token_usage": ai_resp.get("usage"),
                        "tool_input": None,
                        "tool_output": None,
                        "retry_count": ai_resp.get("retry_count", 0),
                        "trace_id": self._trace_id,
                    }
                )
                self._save_snapshot(agent_key, step, messages, logs, context)
                self._save_log(agent_key, goal, "completed", step + 1, tool_calls, logs, started_at)
                if self._notifier:
                    elapsed = (datetime.now() - datetime.fromisoformat(started_at)).total_seconds()
                    self._notifier.notify(agent_key, goal, "completed", elapsed, self._cost_tracker)
                self._checkpoint.delete(agent_key, goal)
                self._stats["total_runs"] += 1
                self._stats["success_count"] += 1
                return RuntimeResult(
                    status="completed",
                    result=decision.get("reasoning", "任务完成"),
                    iterations=step + 1,
                    tool_calls=tool_calls,
                    logs=logs,
                )

            if action == "call_tool" and tool_name:
                try:
                    tool_result = self._tool_registry.call(
                        tool_name, tool_params, self._auth_header, caller_permission=spec.get("max_permission", "read")
                    )
                    self._verifier.verify(tool_result)
                except Exception as e:
                    logs.append(
                        {
                            "step": step,
                            "action": "error",
                            "tool": tool_name,
                            "params": tool_params,
                            "result": str(e),
                            "duration_ms": duration_ms,
                            "llm_prompt": ai_resp.get("prompt"),
                            "llm_raw_response": ai_resp.get("raw_response"),
                            "llm_token_usage": ai_resp.get("usage"),
                            "tool_input": json.dumps(tool_params, ensure_ascii=False),
                            "tool_output": None,
                            "retry_count": ai_resp.get("retry_count", 0),
                            "trace_id": self._trace_id,
                        }
                    )
                    self._save_snapshot(agent_key, step, messages, logs, context, "failed")
                    rolled_back = self._try_rollback(agent_key)
                    if rolled_back:
                        messages, logs, context = rolled_back
                        continue
                    raise

                if tool_result.get("needs_approval"):
                    # 先保存检查点，以便恢复后能找到已批准的审批
                    self._checkpoint.save(
                        agent_key,
                        goal,
                        {
                            "trace_id": self._trace_id,
                            "step": step,
                            "messages": messages,
                            "logs": logs,
                            "tool_calls_so_far": tool_calls,
                            "goal": goal,
                            "agent_key": agent_key,
                            "context": None,
                            "trace": self._trace_data,
                        },
                        self._trace_id,
                    )
                    approval_id = self._approval.create(self._trace_id, agent_key, goal, step, tool_name, tool_params, decision.get("reasoning", ""))
                    self._save_log(agent_key, goal, "awaiting_approval", step, tool_calls, logs, started_at)
                    if self._notifier:
                        elapsed = (datetime.now() - datetime.fromisoformat(started_at)).total_seconds()
                        self._notifier.notify(agent_key, goal, "awaiting_approval", elapsed, self._cost_tracker)
                    return RuntimeResult(
                        status="awaiting_approval",
                        result=f"需要人工审批: {tool_name}",
                        iterations=step,
                        tool_calls=tool_calls,
                        logs=logs,
                        metadata={"approval_id": approval_id, "trace_id": self._trace_id},
                    )

                tool_calls += 1
                tool_output_text = json.dumps(tool_result, ensure_ascii=False)
                safe_output = sanitize_tool_output(tool_output_text)
                logs.append(
                    {
                        "step": step,
                        "action": "call_tool",
                        "tool": tool_name,
                        "params": tool_params,
                        "result": safe_output,
                        "duration_ms": duration_ms,
                        "llm_prompt": ai_resp.get("prompt"),
                        "llm_raw_response": ai_resp.get("raw_response"),
                        "llm_token_usage": ai_resp.get("usage"),
                        "tool_input": json.dumps(tool_params, ensure_ascii=False),
                        "tool_output": tool_output_text,
                        "retry_count": ai_resp.get("retry_count", 0),
                        "trace_id": self._trace_id,
                    }
                )
                messages.append(
                    {
                        "role": "assistant",
                        "content": json.dumps(decision.model_dump() if hasattr(decision, "model_dump") else decision, ensure_ascii=False),
                    }
                )
                messages.append({"role": "user", "content": f"工具返回：{safe_output}"})

                # 循环检测
                self._loop_detector.record(decision)
                loop_result = self._loop_detector.detect()
                if loop_result:
                    logs.append(
                        {
                            "step": step,
                            "action": "loop_detected",
                            "tool": tool_name,
                            "params": tool_params,
                            "result": loop_result,
                            "duration_ms": duration_ms,
                            "trace_id": self._trace_id,
                        }
                    )
                    self._save_log(agent_key, goal, "escalated", step + 1, tool_calls, logs, started_at)
                    self._stats["total_runs"] += 1
                    self._stats["fail_count"] += 1
                    return RuntimeResult(
                        status="escalated",
                        result=f"检测到循环: {loop_result}",
                        iterations=step + 1,
                        tool_calls=tool_calls,
                        logs=logs,
                    )

                if action == "call_tool" and step != start_step:
                    self._checkpoint.save(
                        agent_key,
                        goal,
                        {
                            "trace_id": self._trace_id,
                            "step": step,
                            "messages": messages,
                            "logs": logs,
                            "tool_calls_so_far": tool_calls,
                            "goal": goal,
                            "agent_key": agent_key,
                            "context": context,
                            "trace": self._trace_data,
                        },
                        self._trace_id,
                    )
                self._save_snapshot(agent_key, step, messages, logs, context)
            else:
                logs.append(
                    {
                        "step": step,
                        "action": "error",
                        "tool": tool_name,
                        "params": tool_params,
                        "result": f"invalid action: {action}",
                        "duration_ms": duration_ms,
                        "llm_prompt": ai_resp.get("prompt"),
                        "llm_raw_response": ai_resp.get("raw_response"),
                        "llm_token_usage": ai_resp.get("usage"),
                        "tool_input": None,
                        "tool_output": None,
                        "retry_count": ai_resp.get("retry_count", 0),
                        "trace_id": self._trace_id,
                    }
                )

        self._save_log(agent_key, goal, "max_iterations", max_iter, tool_calls, logs, started_at)
        if self._notifier:
            elapsed = (datetime.now() - datetime.fromisoformat(started_at)).total_seconds()
            self._notifier.notify(agent_key, goal, "max_iterations", elapsed, self._cost_tracker)
        self._stats["total_runs"] += 1
        self._stats["fail_count"] += 1
        return RuntimeResult(
            status="max_iterations",
            result="达到最大迭代次数",
            iterations=max_iter,
            tool_calls=tool_calls,
            logs=logs,
        )

    @staticmethod
    def _estimate_token_count(messages: list[dict]) -> int:
        total = 0
        for msg in messages:
            total += len(msg.get("content", "")) // 4
            total += len(msg.get("role", "")) // 4
        return total

    def _compress_messages(self, messages: list[dict]) -> list[dict]:
        if self._estimate_token_count(messages) < 4000:
            return messages
        compressed = [m for m in messages if m["role"] == "system"]
        recent = [m for m in messages if m["role"] != "system"][-6:]
        compressed.extend(recent)
        if compressed:
            compressed[0]["content"] += f"\n\n[上下文已压缩。保留了最近{len(recent) // 2}轮对话。当前步骤：继续执行。]"
        return compressed

    def _raw_llm_call(self, request_body: dict) -> dict:
        req = urllib.request.Request(
            "http://localhost:8000/ai/chat",
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": self._auth_header,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as rp:
            return json.loads(rp.read().decode("utf-8"))

    def _call_ai(self, messages: list[dict], temperature: float, step: int = 0) -> dict:
        prompt_text = json.dumps(messages, ensure_ascii=False)
        input_len = len(prompt_text)
        call_start = time.time()

        request_body = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048,
        }
        fn = partial(self._raw_llm_call, request_body)
        result = retry_with_backoff(fn, max_attempts=4, base_delay=1.0)

        duration_s = round(time.time() - call_start, 3)

        if result["success"]:
            ai_response = result["data"]
            data = ai_response.get("data", {})
            raw_response = json.dumps(ai_response, ensure_ascii=False)
            output_len = len(raw_response)

            self._trace_data.append(
                {
                    "step": step,
                    "input_len": input_len,
                    "output_len": output_len,
                    "duration_s": duration_s,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return {
                "reply": data.get("reply", ""),
                "usage": data.get("usage", {}),
                "prompt": prompt_text,
                "raw_response": raw_response,
                "retry_count": result["attempts"] - 1,
            }
        raise RuntimeError(f"LLM call failed after {result['attempts']} attempts: {result['error']}")

    def _save_log(self, agent_key, goal, status, iterations, tool_calls, logs, started_at):
        try:
            self._agent_db.execute("ALTER TABLE agent_runtime_logs ADD COLUMN cost_data TEXT DEFAULT '{}'")
        except Exception:
            pass
        self._agent_db.execute(
            "INSERT INTO agent_runtime_logs (agent_key, goal, status, iterations, tool_calls, log_detail, "
            "started_at, completed_at, trace_id, cost_data) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                agent_key,
                goal,
                status,
                iterations,
                tool_calls,
                json.dumps(logs, ensure_ascii=False),
                started_at,
                datetime.now().isoformat(),
                self._trace_id,
                json.dumps(self._cost_tracker),
            ),
        )
        self._agent_db.commit()

    def resume(self, agent_key: str, goal: str, auth_header: str) -> RuntimeResult:
        checkpoint = self._checkpoint.load(agent_key, goal)
        if not checkpoint:
            return RuntimeResult(status="error", result="no checkpoint found", iterations=0, tool_calls=0, logs=[])

        approval = self._agent_db.execute(
            "SELECT * FROM agent_runtime_approvals WHERE trace_id=? AND status='approved' ORDER BY id DESC LIMIT 1",
            (checkpoint["trace_id"],),
        ).fetchone()

        if not approval:
            return RuntimeResult(status="awaiting_approval", result="still pending approval", iterations=0, tool_calls=0, logs=[])

        self._trace_id = checkpoint["trace_id"]
        self._auth_header = auth_header
        return self.execute(goal, agent_key, checkpoint.get("context"))

    def get_status(self) -> dict:
        cur = self._agent_db.execute("SELECT status, COUNT(*) as cnt FROM agent_runtime_logs GROUP BY status")
        by_status = {r["status"]: r["cnt"] for r in cur.fetchall()}
        return {
            **self._stats,
            "by_status": by_status,
        }

    def _save_snapshot(self, agent_key, step, plan, results, context, status="active"):
        try:
            self._snapshot_manager.save(agent_key, step, plan, results, context, status)
        except Exception:
            pass

    def _restore_from_snapshot(self, snapshot_id):
        data = self._snapshot_manager.load(snapshot_id)
        if data is None:
            return None
        return data

    def _try_rollback(self, agent_key):
        latest = self._snapshot_manager.get_latest(agent_key)
        if latest is None:
            return None
        self._snapshot_manager.mark_rolled_back(latest["id"])
        return (latest["plan"], latest["results"], latest["context"])

    def rollback_to(self, snapshot_id):
        data = self._restore_from_snapshot(snapshot_id)
        if data is None:
            return None
        self._snapshot_manager.mark_rolled_back(snapshot_id)
        return (data["plan"], data["results"], data["context"])

    def list_snapshots(self, agent_key, limit=10):
        return self._snapshot_manager.list_snapshots(agent_key, limit)

    def get_cost_usage(self) -> dict:
        return self._cost_governor.get_usage()

    @property
    def brain(self) -> AgentBrain:
        return self._brain
