"""SafetyProfile — 安全配置文件，定义 Agent 的安全边界。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentSafetyProfile:
    """Agent 安全配置文件，定义工具、主题、轮次及人工审核约束。"""

    allowed_tools: list[str] = field(default_factory=list)
    blocked_topics: list[str] = field(default_factory=list)
    max_turns_per_session: int = 50
    requires_human_review: bool = False

    @staticmethod
    def from_safety_level(level: str, allowed_tools: list[str] | None = None) -> AgentSafetyProfile:
        """从 safety_level 字符串映射为 SafetyProfile 实例。"""
        tools = allowed_tools or []
        if level == "read":
            return AgentSafetyProfile(
                allowed_tools=tools,
                blocked_topics=["write", "delete", "admin", "修改", "删除", "写入"],
                max_turns_per_session=100,
                requires_human_review=False,
            )
        if level == "write":
            return AgentSafetyProfile(
                allowed_tools=tools,
                blocked_topics=["admin", "管理员"],
                max_turns_per_session=50,
                requires_human_review=True,
            )
        if level == "admin":
            return AgentSafetyProfile(
                allowed_tools=tools,
                blocked_topics=[],
                max_turns_per_session=200,
                requires_human_review=False,
            )
        return AgentSafetyProfile(allowed_tools=tools)

    def check_topic(self, message: str) -> str | None:
        """检查消息是否包含被阻止的话题。返回第一个匹配的 blocked_topic 或 None。"""
        lower = message.lower()
        for topic in self.blocked_topics:
            if topic.lower() in lower:
                return topic
        return None

    def llm_audit_placeholder(self, message: str) -> bool:
        """LLM 审核占位 — 返回 True 表示通过（待接入真实 LLM 审核）。"""
        return True
