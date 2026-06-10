"""LangGraph 测试路由：用于验证图编排流水线的测试端点。"""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/api/langgraph", tags=["langgraph"])


class TestRequest(BaseModel):
    """测试请求体。"""

    input_message: str = ""


@router.post("/test", tags=["langgraph"])
def run_test_graph(body: TestRequest, _: dict = Depends(require_scope("visit"))):
    from cloud.langgraph.graph import get_test_graph

    graph = get_test_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_message = body.input_message or "hello"
    result = graph.invoke(
        {"messages": [initial_message], "next_agent": "", "metadata": {}},
        config,
    )
    return success(data={
        "thread_id": thread_id,
        "messages": result["messages"],
        "status": "completed",
    })
