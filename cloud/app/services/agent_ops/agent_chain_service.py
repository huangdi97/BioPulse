"""Agent 联动链引擎 — 读 YAML 配置，监听事件总线，自动触发下游 Agent。"""

import logging
import os
import threading
from typing import Any

import yaml

from cloud.app.agent_runtime.core.runtime_core import RuntimeCore
from cloud.app.database import DB_PATH

logger = logging.getLogger(__name__)

_CHAINS: list[dict] = []
_LOCK = threading.Lock()
_ACTIVE_RUNS: dict[str, threading.Thread] = {}


def _load_chains() -> list[dict]:
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "agents", "trigger_chains.yaml")
    alt_path = os.path.join(os.path.dirname(__file__), "..", "agents", "trigger_chains.yaml")
    for path in (config_path, alt_path):
        if os.path.isfile(path):
            with open(path) as f:
                data = yaml.safe_load(f)
            logger.info("AgentChainService loaded %d chains from %s", len(data.get("chains", [])), path)
            return data.get("chains", [])
    logger.warning("AgentChainService: trigger_chains.yaml not found")
    return []


def reload_chains() -> None:
    global _CHAINS
    chains = _load_chains()
    with _LOCK:
        _CHAINS = chains


def on_event(event_type: str, payload: dict | None = None) -> None:
    with _LOCK:
        chains = list(_CHAINS)
    matched = [c for c in chains if c.get("trigger_event") == event_type]
    if not matched:
        return
    for chain in matched:
        _run_chain_async(chain, payload)


def _run_chain_async(chain: dict, payload: dict | None) -> None:
    def _run():
        chain_name = chain.get("name", "unnamed")
        steps = chain.get("steps", [])
        logger.info("AgentChainService starting chain=%s (%d steps)", chain_name, len(steps))
        step_results: dict[str, Any] = {}
        for step in steps:
            agent = step.get("agent", "")
            action = step.get("action", "")
            wait_for = step.get("wait_for")
            condition = step.get("condition")
            timeout = step.get("timeout", 60)
            if wait_for and wait_for not in step_results:
                logger.warning("Chain=%s step=%s wait_for=%s not ready, skipping", chain_name, agent, wait_for)
                continue
            condition_ok = True
            if condition:
                condition_ok = _evaluate_condition(condition, step_results)
                if not condition_ok:
                    logger.info("Chain=%s step=%s condition not met, skipping", chain_name, agent)
                    continue
            result = _trigger_agent(agent, action, payload, step_results, timeout)
            step_results[agent] = result
            logger.info("Chain=%s step=%s completed status=%s", chain_name, agent, result.get("status"))
        logger.info("AgentChainService chain=%s completed", chain_name)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    chain_name = chain.get("name", "unnamed")
    with _LOCK:
        _ACTIVE_RUNS[chain_name] = thread


def _trigger_agent(
    agent_key: str,
    action: str,
    payload: dict | None,
    step_results: dict[str, Any],
    timeout: int,
) -> dict:
    import sqlite3

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        context = {"action": action, "event_payload": payload, "step_results": step_results}
        runtime = RuntimeCore(conn, conn, "", agent_key)
        result = runtime.execute(action, agent_key, context)
        return {"status": result.status, "output": str(result.output) if hasattr(result, "output") else ""}
    except Exception:
        logger.exception("AgentChainService agent=%s action=%s failed", agent_key, action)
        return {"status": "error"}
    finally:
        conn.close()


def _evaluate_condition(condition: str, step_results: dict[str, Any]) -> bool:
    if "compliance_violation" in condition:
        return any("violation" in str(r.get("output", "")).lower() for r in step_results.values())
    return True


def init_agent_chains() -> None:
    reload_chains()
    logger.info("AgentChainService initialized with %d chains", len(_CHAINS))


init_agent_chains()
