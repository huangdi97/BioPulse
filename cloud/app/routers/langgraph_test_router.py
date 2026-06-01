import uuid
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/langgraph", tags=["langgraph"])


class TestRequest(BaseModel):
    input_message: str = ""


@router.post("/test")
def run_test_graph(body: TestRequest):
    from cloud.langgraph.graph import get_test_graph

    graph = get_test_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_message = body.input_message or "hello"
    result = graph.invoke(
        {"messages": [initial_message], "next_agent": "", "metadata": {}},
        config,
    )
    return {
        "code": 0,
        "data": {
            "thread_id": thread_id,
            "messages": result["messages"],
            "status": "completed",
        },
        "message": "success",
    }
