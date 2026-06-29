"""Agent 独立容器入口 — 根据 AGENT_NAME 环境变量启动对应 Agent 的 HTTP 服务。
支持 Disposable Agents 模式：启动时从 DurableExecutor 恢复上次状态，无则新建。
"""

import logging
import os

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from cloud.app.agent_runtime.core.agent_registry import AgentRegistry
from cloud.app.agent_runtime.core.agent_specs import AGENT_SPECS
from cloud.app.agent_runtime.core.durable_execution import DurableExecutor
from cloud.app.agent_runtime.core.runtime_core import RuntimeCore
from cloud.app.database import DB_PATH

logger = logging.getLogger(__name__)

app = FastAPI(title="Agent Container", version="1.0.0")

AGENT_NAME = os.environ.get("AGENT_NAME", "")
AGENT_PORT = int(os.environ.get("AGENT_PORT", "8015"))


def restore_or_create() -> list[dict]:
    """启动时检查 DurableExecutor 是否有未完成执行，有则恢复，无则新建。

    Returns:
        待恢复的 pending 执行列表（每个元素含 agent_key / trace_id / step / last_active）。
        空列表表示无待恢复任务。
    """
    executor = DurableExecutor()
    pending = executor.list_pending()
    agent_pending = [p for p in pending if p["agent_key"] == AGENT_NAME]
    if agent_pending:
        logger.info(
            "Found %d pending execution(s) for agent '%s' — restoring from checkpoint",
            len(agent_pending),
            AGENT_NAME,
        )
        for p in agent_pending:
            state = executor.restore(p["agent_key"], p["trace_id"])
            if state:
                logger.info(
                    "Restored agent=%s trace=%s step=%d (last_active=%.1f)",
                    p["agent_key"],
                    p["trace_id"],
                    p["step"],
                    p["last_active"],
                )
            else:
                logger.warning("No checkpoint data for agent=%s trace=%s", p["agent_key"], p["trace_id"])
    else:
        logger.info("No pending executions for agent '%s' — ready for new work", AGENT_NAME)
    return agent_pending


class ExecuteRequest(BaseModel):
    goal: str
    context: dict | None = None


@app.on_event("startup")
def _on_startup():
    """Agent 容器启动时自动执行 restore_or_create — 检查并恢复未完成执行。
    同时加载 AgentRegistry 身份，确保 Harness 四层校验（ToolBridge 白名单/Memory namespace/OutputSchema/证据溯源）生效。
    """
    AgentRegistry.load()
    pending = restore_or_create()
    if pending:
        logger.info("Agent '%s' resumed with %d pending executions(s)", AGENT_NAME, len(pending))


@app.post("/execute")
def execute(body: ExecuteRequest):
    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        runtime = RuntimeCore(conn, conn, AGENT_NAME, AGENT_NAME)
        result = runtime.execute(body.goal, AGENT_NAME, body.context)
        return result.model_dump()
    finally:
        conn.close()


@app.get("/health")
def health():
    return {"status": "ok", "agent": AGENT_NAME}


@app.get("/spec")
def spec():
    return AGENT_SPECS.get(AGENT_NAME, {})


def main():
    if AGENT_NAME not in AGENT_SPECS:
        logger.info("Unknown AGENT_NAME: %s. Available: %s", AGENT_NAME, list(AGENT_SPECS.keys()))
        return
    logger.info("Starting agent container: %s on port %d", AGENT_NAME, AGENT_PORT)
    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)


if __name__ == "__main__":
    main()
