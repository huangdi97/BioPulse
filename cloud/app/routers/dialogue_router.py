"""对话层路由 — 用户与系统之间的双向交流 API。"""

import logging

from fastapi import APIRouter

from cloud.app.agent_runtime.dialogue_manager import DialogueTranslator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dialogue", tags=["dialogue"])

_translator = DialogueTranslator()


@router.post("/session")
def create_session(agent_key: str, user_id: str, context: dict | None = None):
    """创建新对话 session。"""
    session_id = _translator.create_session(agent_key, user_id, context)
    return {"session_id": session_id}


@router.post("/send")
def send_message(session_id: str, message: str):
    """发送消息，返回翻译后的回复。"""
    reply = _translator.translate(session_id, message)
    return {"reply": reply}


@router.get("/history/{session_id}")
def get_history(session_id: str, limit: int = 10):
    """获取对话历史。"""
    history = _translator.get_history(session_id, limit)
    return {"history": history}


@router.post("/feedback")
def submit_feedback(
    feedback_type: str,
    target_id: str,
    content: str,
    session_id: str | None = None,
):
    """提交用户反馈（误报/不够好等）。"""
    logger.info(
        "用户反馈: type=%s target=%s content=%s",
        feedback_type,
        target_id,
        content[:50],
    )
    return {"status": "received", "message": "反馈已记录"}
