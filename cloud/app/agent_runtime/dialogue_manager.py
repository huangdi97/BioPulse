"""多轮对话管理器 — 对话状态机与会话管理。"""

import time
import uuid
from enum import Enum


class DialogueState(str, Enum):
    idle = "idle"
    listening = "listening"
    processing = "processing"
    responding = "responding"
    completed = "completed"
    error = "error"


class DialogueSession:
    """单个对话会话。"""

    def __init__(self, session_id: str, agent_key: str, user_id: str):
        self.session_id = session_id
        self.agent_key = agent_key
        self.user_id = user_id
        self.state = DialogueState.idle
        self.messages: list[dict] = []
        self.context: dict = {}
        self.created_at = time.time()
        self.updated_at = time.time()

    def touch(self) -> None:
        self.updated_at = time.time()

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content, "timestamp": time.time()})
        if role == "user":
            self.state = DialogueState.processing
        elif role == "assistant":
            self.state = DialogueState.responding
        self.touch()

    def close(self) -> None:
        self.state = DialogueState.completed
        self.touch()

    def recent_context(self, n: int = 5) -> list[dict]:
        return self.messages[-n * 2:] if len(self.messages) > n * 2 else self.messages

    def is_stale(self, max_idle_minutes: int = 30) -> bool:
        return (time.time() - self.updated_at) > max_idle_minutes * 60


class DialogueManager:
    """管理所有对话会话的创建、状态转换和清理。"""

    def __init__(self):
        self._sessions: dict[str, DialogueSession] = {}

    def create_session(self, agent_key: str, user_id: str) -> str:
        session_id = str(uuid.uuid4())[:8]
        self._sessions[session_id] = DialogueSession(session_id, agent_key, user_id)
        return session_id

    def get_session(self, session_id: str) -> DialogueSession | None:
        return self._sessions.get(session_id)

    def add_message(self, session_id: str, role: str, content: str) -> DialogueSession | None:
        session = self._sessions.get(session_id)
        if session and session.state not in (DialogueState.completed, DialogueState.error):
            session.add_message(role, content)
        return session

    def close_session(self, session_id: str) -> None:
        session = self._sessions.get(session_id)
        if session:
            session.close()

    def cleanup_stale(self, max_idle_minutes: int = 30) -> int:
        stale = [sid for sid, s in self._sessions.items()
                 if s.state not in (DialogueState.completed, DialogueState.error)
                 and (time.time() - s.updated_at) > max_idle_minutes * 60]
        for sid in stale:
            self._sessions[sid].close()
        return len(stale)

    def get_context(self, session_id: str, n: int = 5) -> dict:
        session = self._sessions.get(session_id)
        if not session:
            return {}
        return {
            "session_id": session.session_id,
            "agent_key": session.agent_key,
            "state": session.state.value,
            "recent_messages": session.recent_context(n),
            "context": session.context,
        }
