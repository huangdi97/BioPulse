"""Agent 独立容器入口 — 根据 AGENT_NAME 环境变量启动对应 Agent 的 HTTP 服务。"""

import logging
import os

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from cloud.app.agent_runtime.agent_specs import AGENT_SPECS
from cloud.app.agent_runtime.runtime_core import RuntimeCore
from cloud.app.database import DB_PATH

app = FastAPI(title="Agent Container", version="1.0.0")

AGENT_NAME = os.environ.get("AGENT_NAME", "")
AGENT_PORT = int(os.environ.get("AGENT_PORT", "8015"))


class ExecuteRequest(BaseModel):
    goal: str
    context: dict | None = None


@app.post("/execute")
def execute(body: ExecuteRequest):
    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        runtime = RuntimeCore(conn, conn, "")
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
