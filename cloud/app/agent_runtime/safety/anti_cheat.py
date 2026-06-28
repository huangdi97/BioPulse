"""Anti-Cheat — 检测 Agent 通过不当手段达成目标：删数据、跳过验证、指标操纵。"""

import logging
import os

from cloud.app.agent_runtime.core.shared_state import SharedStateEntry, get_shared_state

logger = logging.getLogger(__name__)

_AUDIT_LOG_FILE = os.environ.get("ANTICHEAT_AUDIT_LOG", "data/anticheat_audit.log")

DANGEROUS_TOOL_PATTERNS: dict[str, list[str]] = {
    "delete": ["delete", "remove", "drop", "truncate", "purge"],
    "disable_safety": ["disable", "bypass", "skip", "override", "suppress"],
    "skip_validation": ["skip_validation", "force", "ignore_errors", "no_verify"],
}


class AntiCheat:
    """反作弊检查 — 工具滥用 / 指标操纵 / 跳过关键步骤。"""

    def check_tool_abuse(self, agent_key: str, tool_name: str, params: dict | None = None) -> dict:
        """检测危险工具调用模式。返回 {"flagged": bool, "reason": str, "severity": str}。"""
        name_lower = tool_name.lower()
        param_str = str(params or {}).lower()

        for category, patterns in DANGEROUS_TOOL_PATTERNS.items():
            for p in patterns:
                if p in name_lower or p in param_str:
                    severity = "critical" if category == "delete" else "high"
                    reason = f"Tool abuse detected: {tool_name} matches '{p}' ({category})"
                    self._audit_log(agent_key, reason, severity)
                    return {"flagged": True, "reason": reason, "severity": severity}

        return {"flagged": False, "reason": "", "severity": "none"}

    def check_metric_gaming(self, agent_key: str, metric_name: str, value: float) -> dict:
        """检测指标异常 — 突然"完美"可能意味着作弊。"""
        thresholds = {
            "success_rate": (0.99, 1.01),
            "test_pass_rate": (0.98, 1.01),
            "confidence": (0.95, 1.01),
            "completion_rate": (0.98, 1.01),
        }

        threshold = thresholds.get(metric_name)
        if threshold and threshold[0] <= value <= threshold[1]:
            reason = f"Metric gaming suspected: {metric_name}={value} is suspiciously perfect"
            self._audit_log(agent_key, reason, "high")
            return {"flagged": True, "reason": reason, "severity": "high"}

        return {"flagged": False, "reason": "", "severity": "none"}

    def check_shortcuts(self, agent_key: str, plan: dict | None, execution_log: list[dict] | None) -> dict:
        """检测 Agent 是否跳过关键步骤（如 validation / approval / review）。"""
        if not plan or not execution_log:
            return {"flagged": False, "reason": "", "severity": "none"}

        steps = plan.get("steps", [])
        skipped_steps: list[str] = []

        for step in steps:
            step_desc = (step.get("description") or "").lower()
            step_id = step.get("step_id", "?")
            if any(kw in step_desc for kw in ["verify", "validate", "approve", "review", "check", "audit"]):
                if not self._step_was_executed(step_id, execution_log):
                    skipped_steps.append(step_id)

        if skipped_steps:
            reason = f"Shortcut detected: skipped critical steps {skipped_steps}"
            self._audit_log(agent_key, reason, "high")
            return {"flagged": True, "reason": reason, "severity": "high"}

        return {"flagged": False, "reason": "", "severity": "none"}

    def intercept(self, agent_key: str, tool_name: str, params: dict | None) -> dict | None:
        """拦截检查 — ToolBridge 调用前执行。返回 None 放行，返回 dict 则拦截 + 强制 HITL。"""
        abuse = self.check_tool_abuse(agent_key, tool_name, params)
        if abuse["flagged"]:
            self._write_intercept_event(agent_key, tool_name, params, abuse)
            return {
                "success": False,
                "data": None,
                "error": f"Blocked by anti-cheat: {abuse['reason']}",
                "needs_approval": True,
                "severity": abuse["severity"],
            }
        return None

    @staticmethod
    def _step_was_executed(step_id: str, execution_log: list[dict]) -> bool:
        for entry in execution_log:
            if entry.get("step_id") == step_id or entry.get("step") == step_id:
                return True
        return False

    @staticmethod
    def _audit_log(agent_key: str, reason: str, severity: str) -> None:
        import time

        line = f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}] {severity.upper()} {agent_key}: {reason}"
        logger.warning("ANTI-CHEAT: %s", line)
        os.makedirs(os.path.dirname(_AUDIT_LOG_FILE) or ".", exist_ok=True)
        try:
            with open(_AUDIT_LOG_FILE, "a") as f:
                f.write(line + "\n")
        except OSError:
            pass

    @staticmethod
    def _write_intercept_event(agent_key: str, tool_name: str, params: dict | None, abuse: dict) -> None:
        entry = SharedStateEntry(
            namespace="safety.anticheat",
            key=f"intercept.{agent_key}",
            value={
                "agent_key": agent_key,
                "tool_name": tool_name,
                "params": params,
                "reason": abuse["reason"],
                "severity": abuse["severity"],
            },
            agent_key=agent_key,
        )
        get_shared_state().write(entry, caller_agent_key=agent_key)
