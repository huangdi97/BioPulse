"""Agent 运行时辅助方法，包含 LLM 调用、快照管理、Token 估算等。"""

import json
import time
import urllib.request
from datetime import datetime
from functools import partial

from cloud.app.agent_runtime.retry import retry_with_backoff


class RuntimeHelper:
    """AgentRuntime 的父类，提供 LLM 调用、快照管理等辅助方法。"""

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
