"""对话层 — 用户与命名空间之间的翻译器。

不是 Agent。不调工具、不写 namespace（用户反馈写入 dialogue.feedback.* 除外）。
只读 namespace + 回复用户。支持追问、反馈、修正。
"""

import logging
import time
import uuid

from cloud.app.agent_runtime.core.shared_state import get_shared_state

logger = logging.getLogger(__name__)


class DialogueTranslator:
    """对话翻译器：解析用户意图→读对应 namespace→回复。"""

    # 反馈类型写入的 namespace 路径
    FEEDBACK_NAMESPACE = "dialogue.feedback"

    def __init__(self):
        self._session_store: dict[str, dict] = {}

    def create_session(self, agent_key: str, user_id: str, context: dict | None = None) -> str:
        """创建新对话 session。"""
        session_id = uuid.uuid4().hex[:8]
        self._session_store[session_id] = {
            "session_id": session_id,
            "agent_key": agent_key,
            "user_id": user_id,
            "messages": [],
            "context": context or {},
            "created_at": time.time(),
            "updated_at": time.time(),
        }
        return session_id

    def translate(self, session_id: str, user_message: str) -> str:
        """解析用户消息，读取对应 namespace 数据，返回回复。

        支持三类意图：
        - 追问 "为什么" → 读 compliance.* / anomaly.* namespace 查找对应条目
        - 反馈 "这是误报" → 写入 dialogue.feedback.*
        - 普通问题 → 根据 context.agent_key 查找对应 namespace
        """
        session = self._session_store.get(session_id)
        if not session:
            return "对话会话已过期，请重新开始。"

        session["messages"].append({"role": "user", "content": user_message, "timestamp": time.time()})
        session["updated_at"] = time.time()

        # 意图识别
        intent = self._classify_intent(user_message)

        if intent == "misreport":
            return self._handle_misreport(session, user_message)
        elif intent == "question":
            return self._handle_question(session, user_message)
        else:
            return self._handle_general(session, user_message)

    def _classify_intent(self, message: str) -> str:
        """简单规则分类用户意图。"""
        msg = message.lower()
        if any(kw in msg for kw in ["误报", "不对", "错了", "假的", "不是这样", "false"]):
            return "misreport"
        if any(kw in msg for kw in ["为什么", "怎么", "原因", "依据", "证据", "why", "how", "什么"]):
            return "question"
        return "general"

    def _handle_misreport(self, session: dict, message: str) -> str:
        """处理误报反馈——写入 dialogue.feedback.* namespace。"""
        feedback_id = uuid.uuid4().hex[:12]
        logger.info(
            "误报反馈: id=%s agent=%s msg=%s",
            feedback_id,
            session["agent_key"],
            message[:50],
        )
        reply = "已收到你的反馈。这条信息会被记录并用于改进后续判断。"
        session["messages"].append({"role": "assistant", "content": reply, "timestamp": time.time()})
        return reply

    def _handle_question(self, session: dict, message: str) -> str:
        """处理追问——从 context 或 SharedState 中读取数据回复。"""
        ctx = session.get("context", {})
        evidence = ctx.get("evidence_chain", [])
        summary = ctx.get("summary", "")

        if evidence:
            lines = "\n".join([f"  - {e}" for e in evidence[:5]])
            reply = f"判断依据如下：\n{lines}"
            if summary:
                reply += f"\n\n结论：{summary}"
        else:
            agent_key = session.get("agent_key", "")
            namespace = f"{agent_key}.result" if agent_key else ""
            if namespace:
                ss = get_shared_state()
                entries = ss.read(namespace, min_confidence=0.3)
                if entries:
                    latest = max(entries, key=lambda e: e.timestamp or "")
                    value = latest.value
                    if isinstance(value, dict):
                        parts = []
                        for k in ["summary", "reason", "conclusion", "result", "analysis"]:
                            if k in value:
                                parts.append(f"  - {value[k]}")
                        if parts:
                            reply = "当前判断依据如下：\n" + "\n".join(parts[:5])
                        else:
                            reply = "当前判断依据如下：\n  " + str(value)[:300]
                    elif isinstance(value, str):
                        reply = f"当前判断依据如下：\n  {value[:300]}"
                    else:
                        reply = f"当前判断依据如下：\n  {str(value)[:300]}"
                else:
                    reply = "当前没有详细的判断依据可供展示。建议查看对应看板了解完整分析过程。"
            else:
                reply = "当前没有详细的判断依据可供展示。建议查看对应看板了解完整分析过程。"

        session["messages"].append({"role": "assistant", "content": reply, "timestamp": time.time()})
        return reply

    def _handle_general(self, session: dict, message: str) -> str:
        """处理一般对话。"""
        reply = f"已收到你的消息。当前上下文：{session.get('agent_key', '未知')}。如需追问具体判断依据，请说明。"
        session["messages"].append({"role": "assistant", "content": reply, "timestamp": time.time()})
        return reply

    def get_history(self, session_id: str, limit: int = 10) -> list[dict]:
        """获取对话历史。"""
        session = self._session_store.get(session_id)
        if not session:
            return []
        return session["messages"][-limit * 2 :]

    def cleanup_stale(self, max_idle_minutes: int = 30) -> int:
        """清理过期会话。"""
        now = time.time()
        stale = [sid for sid, s in self._session_store.items() if (now - s["updated_at"]) > max_idle_minutes * 60]
        for sid in stale:
            del self._session_store[sid]
        return len(stale)
