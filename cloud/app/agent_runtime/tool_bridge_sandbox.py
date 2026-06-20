"""工具桥接沙箱执行。"""

from __future__ import annotations

import subprocess

from .tool_bridge_utils import idempotency_key, set_idempotency


def run_sandboxed(tool_name: str, params: dict, idempotency_agent: str | None, idempotency_step: int, cache: dict) -> dict:
    """Execute a tool script in a subprocess sandbox with idempotency support."""
    script = params.pop("_script", "")
    if not script:
        return {"success": False, "data": None, "error": "sandbox tool requires _script param", "needs_approval": False}
    try:
        completed = subprocess.run(
            script,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        result = {
            "success": completed.returncode == 0,
            "data": completed.stdout,
            "error": completed.stderr if completed.returncode != 0 else None,
        }
        if idempotency_agent:
            set_idempotency(cache, idempotency_key(idempotency_agent, tool_name, idempotency_step), result)
        return result
    except subprocess.TimeoutExpired:
        return {"success": False, "data": None, "error": "sandbox execution timed out after 30s", "needs_approval": False}
    except Exception as e:
        return {"success": False, "data": None, "error": f"sandbox execution failed: {e}", "needs_approval": False}
