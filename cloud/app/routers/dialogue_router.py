"""对话层路由 — 用户与系统之间的双向交流 API。
用户跟"系统"对话，系统内部调 Agent。对话层是用户与 Agent 命名空间之间的翻译器。
"""

import json
import logging
import uuid

from fastapi import APIRouter
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from cloud.app.services.rep_workbench.dialogue_service import DialogueTranslator, SharedStateEntry, get_shared_state

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dialogue", tags=["dialogue"])

_translator = DialogueTranslator()


class DialogueRequest(BaseModel):
    message: str
    session_id: str | None = None
    user_id: str = "anonymous"
    agent_key: str | None = None
    stream: bool = False


class DialogueResponse(BaseModel):
    session_id: str
    reply: str
    source: str = "dialogue"


@router.post("", response_model=DialogueResponse)
async def dialogue(body: DialogueRequest):
    """对话入口：用户发消息 → 解析意图 → 读 SharedState / 调 Agent → SSE 或 JSON 返回。

    请求示例:
        {
          "message": "最近有哪些合规风险？",
          "session_id": null,
          "user_id": "user_001",
          "agent_key": "knowledge_worker",
          "stream": false
        }

    非流式响应:
        {
          "session_id": "d6f8e2a1-b4c3-...",
          "reply": "根据最新数据分析，本月主要合规风险包括...",
          "source": "dialogue"
        }

    流式响应 (text/event-stream):
        event: dialogue.start
        data: {"session_id": "d6f8e2a1-...", "message": "最近有哪些合规风险？"}

        event: dialogue.reply
        data: {"reply": "根据最新数据分析...", "status": "success"}

        event: done
        data: {}
    """
    ss = get_shared_state()
    session_id = body.session_id or _create_session(body)

    # 检查能否从 SharedState 直接答复（追问同一话题）
    cached = _try_read_cached(ss, body.message, body.agent_key)
    if cached:
        if body.stream:
            return _sse_response([{"event": "dialogue.reply", "data": {"reply": cached, "source": "cache"}}])
        return DialogueResponse(session_id=session_id, reply=cached, source="cache")

    # 需要调 Agent 时，流式返回执行过程
    if body.stream:
        return _sse_stream_dialogue(session_id, body)
    reply = _translator.translate(session_id, body.message)
    return DialogueResponse(session_id=session_id, reply=reply, source="dialogue")


def _create_session(body: DialogueRequest) -> str:
    session_id = _translator.create_session(body.agent_key or "knowledge_worker", body.user_id)
    return session_id


def _try_read_cached(ss, message: str, agent_key: str | None) -> str | None:
    """检查 SharedState 中是否有已有结果可直接回复。"""
    msg_lower = message.lower()
    for kw in ["为什么", "怎么", "原因", "依据", "证据", "why", "how", "什么"]:
        if kw in msg_lower:
            namespace = f"{agent_key or 'knowledge'}.result"
            entries = ss.read(namespace, min_confidence=0.3)
            if entries:
                latest = max(entries, key=lambda e: e.timestamp or "")
                return latest.value if isinstance(latest.value, str) else json.dumps(latest.value, ensure_ascii=False)
    for kw in ["误报", "不对", "错了", "假的", "不是这样", "false"]:
        if kw in msg_lower:
            ss.write(
                SharedStateEntry(
                    namespace="dialogue.feedback",
                    key=uuid.uuid4().hex[:12],
                    value=message,
                    agent_key=agent_key or "user",
                    evidence=["user_feedback"],
                ),
                caller_agent_key="dialogue",
            )
            return "已收到你的反馈。这条信息会被记录并用于改进后续判断。"
    return None


def _sse_response(events: list[dict]) -> StreamingResponse:
    async def _generate():
        for ev in events:
            yield f"event: {ev['event']}\ndata: {json.dumps(ev['data'], ensure_ascii=False)}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(_generate(), media_type="text/event-stream")


def _sse_stream_dialogue(session_id: str, body: DialogueRequest) -> StreamingResponse:
    from cloud.app.agent_runtime.core.runtime_core import RuntimeCore

    async def _generate():
        yield f"event: dialogue.start\ndata: {json.dumps({'session_id': session_id, 'message': body.message}, ensure_ascii=False)}\n\n"
        if not body or not body.message:
            yield f"event: dialogue.error\ndata: {json.dumps({'error': '消息内容为空，无法执行'}, ensure_ascii=False)}\n\n"
            yield "event: done\ndata: {}\n\n"
            return
        agent_key = body.agent_key or "knowledge_worker"
        try:
            runtime = RuntimeCore(None, None, "", agent_key)
            from cloud.app.agent_runtime.comm.streamer import AgentStreamer

            streamer = AgentStreamer()
            runtime.set_streamer(streamer)
            trace_id = runtime._trace_id
            result = runtime.execute(body.message, agent_key)
            async for chunk in streamer.get_stream(trace_id):
                yield chunk
            yield f"event: dialogue.reply\ndata: {json.dumps({'reply': result.result, 'status': result.status}, ensure_ascii=False)}\n\n"
            get_shared_state().write(
                SharedStateEntry(
                    namespace=f"{agent_key}.result",
                    key=f"dialogue_{uuid.uuid4().hex[:8]}",
                    value=result.result,
                    agent_key=agent_key,
                    confidence=1.0 if result.status == "success" else 0.5,
                    evidence=["dialogue_execution"],
                ),
                caller_agent_key="dialogue",
            )
        except Exception as e:
            logger.exception("Dialogue execution failed")
            detail = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
            yield f"event: dialogue.error\ndata: {json.dumps({'error': f'对话执行失败: {detail}'}, ensure_ascii=False)}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(_generate(), media_type="text/event-stream")


@router.post("/session")
def create_session(agent_key: str, user_id: str, context: dict | None = None):
    """创建新对话 session。

    请求示例:
        POST /api/v1/dialogue/session?agent_key=knowledge_worker&user_id=user_001

    响应示例:
        {"session_id": "d6f8e2a1-b4c3-4f7e-9a2d-1e5f8c0a3b7c"}
    """
    session_id = _translator.create_session(agent_key, user_id, context)
    return {"session_id": session_id}


@router.post("/send")
def send_message(session_id: str, message: str):
    """发送消息，返回翻译后的回复。

    请求示例:
        {
          "session_id": "d6f8e2a1-b4c3-...",
          "message": "帮我查一下最近的合规风险"
        }

    响应示例:
        {"reply": "根据最新数据分析，本月主要合规风险包括...", "source": "dialogue"}

    Notes:
        - 如果不指定 session_id，系统会自动创建新 session。
        - 内部会优先检查 SharedState 缓存，命中则直接返回 "source": "cache"。
    """
    cached = _try_read_cached(get_shared_state(), message, None)
    if cached:
        return {"reply": cached, "source": "cache"}
    reply = _translator.translate(session_id, message)
    return {"reply": reply}


@router.get("/history/{session_id}")
def get_history(session_id: str, limit: int = 10):
    """获取对话历史。

    请求示例:
        GET /api/v1/dialogue/history/d6f8e2a1-...?limit=5

    响应示例:
        {
          "history": [
            {"role": "user", "content": "帮我查合规风险", "timestamp": "2026-06-29T10:00:00"},
            {"role": "assistant", "content": "根据最新数据分析...", "timestamp": "2026-06-29T10:00:01"}
          ]
        }
    """
    history = _translator.get_history(session_id, limit)
    return {"history": history}


@router.post("/feedback")
def submit_feedback(
    feedback_type: str,
    target_id: str,
    content: str,
    session_id: str | None = None,
):
    """提交用户反馈（误报/不够好等）并写入 SharedState。

    请求示例:
        POST /api/v1/dialogue/feedback?feedback_type=false_positive&target_id=msg_001&content=这条判断不准确

    响应示例:
        {"status": "received", "message": "反馈已记录"}
    """
    feedback_entry = SharedStateEntry(
        namespace="dialogue.feedback",
        key=uuid.uuid4().hex[:12],
        value={"type": feedback_type, "target_id": target_id, "content": content},
        agent_key="user",
        confidence=1.0,
        evidence=["user_feedback"],
    )
    get_shared_state().write(feedback_entry, caller_agent_key="dialogue")
    logger.info("用户反馈已写入 SharedState: type=%s target=%s", feedback_type, target_id)
    return {"status": "received", "message": "反馈已记录"}
