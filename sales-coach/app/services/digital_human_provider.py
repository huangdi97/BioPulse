"""数字人供应商模块，提供多供应商抽象接口及内置/第三方实现。"""

from abc import ABC, abstractmethod
from typing import Any

from sales_coach.app.digital_human import simulate_dialogue


class DigitalHumanProvider(ABC):
    """数字人供应商抽象基类，定义会话创建、消息发送等接口。"""

    @abstractmethod
    def create_session(self, scenario: dict, user_id: int) -> str:
        """创建数字人供应商侧会话。

        Args:
            scenario: 场景信息字典。
            user_id: 用户ID。

        Returns:
            供应商侧会话标识字符串。
        """
        ...

    @abstractmethod
    def send_message(self, session_id: str, message: Any, context: list) -> dict:
        """向供应商侧会话发送消息并获取回复。

        Args:
            session_id: 供应商侧会话标识。
            message: 消息内容。
            context: 对话上下文列表。

        Returns:
            包含AI回复等信息的字典。
        """
        ...

    @abstractmethod
    def end_session(self, session_id: str) -> bool:
        """结束供应商侧会话。

        Args:
            session_id: 供应商侧会话标识。

        Returns:
            操作是否成功。
        """
        ...

    @abstractmethod
    def get_provider_info(self) -> dict:
        """获取供应商信息。

        Returns:
            包含名称、版本、能力及连接状态的字典。
        """
        ...


class InternalLLMProvider(DigitalHumanProvider):
    """内置LLM数字人供应商，使用本地AI网关进行对话模拟。"""

    def create_session(self, scenario: dict, user_id: int) -> str:
        """创建内置LLM供应商侧会话。

        Args:
            scenario: 场景信息字典。
            user_id: 用户ID。

        Returns:
            内置LLM会话ID字符串。
        """
        return f"internal:{scenario.get('id', '')}"

    def send_message(self, session_id: str, message: Any, context: list) -> dict:
        """使用内置LLM发送消息并模拟对话。

        Args:
            session_id: 供应商侧会话标识。
            message: 消息内容，含角色和AI网关地址。
            context: 对话上下文列表。

        Returns:
            包含回复和置信度的字典。
        """
        result = simulate_dialogue(message["role"], context, message["content"], message["ai_gateway_url"])
        return {
            "reply": result["reply"],
            "emotions": {},
            "gestures": {},
            "confidence": 1.0,
        }

    def end_session(self, session_id: str) -> bool:
        return True

    def get_provider_info(self) -> dict:
        return {
            "name": "internal_llm",
            "version": "1.0",
            "capabilities": ["text"],
            "connected": True,
        }


class WaveCloudProvider(DigitalHumanProvider):
    """浪潮云数字人供应商，等待合作接入。"""

    def create_session(self, scenario: dict, user_id: int) -> str:
        """创建浪潮云数字人供应商侧会话（存根）。

        Args:
            scenario: 场景信息字典。
            user_id: 用户ID。

        Returns:
            浪潮云会话存根标识。
        """
        return "wavecloud:stub"

    def send_message(self, session_id: str, message: Any, context: list) -> dict:
        return {
            "provider": "wavecloud",
            "status": "not_connected",
            "message": "等待浪潮云合作接入",
        }

    def end_session(self, session_id: str) -> bool:
        return True

    def get_provider_info(self) -> dict:
        return {
            "name": "wavecloud",
            "version": "0.0",
            "capabilities": [],
            "connected": False,
        }


class MoShangProvider(DigitalHumanProvider):
    """摩熵医药数字人供应商，等待合作接入。"""

    def create_session(self, scenario: dict, user_id: int) -> str:
        return "mosheng:stub"

    def send_message(self, session_id: str, message: Any, context: list) -> dict:
        return {
            "provider": "mosheng",
            "status": "not_connected",
            "message": "等待摩熵医药合作接入",
        }

    def end_session(self, session_id: str) -> bool:
        return True

    def get_provider_info(self) -> dict:
        return {
            "name": "mosheng",
            "version": "0.0",
            "capabilities": [],
            "connected": False,
        }


def get_provider(provider_name: str = "internal") -> DigitalHumanProvider:
    providers = {
        "internal": InternalLLMProvider,
        "wavecloud": WaveCloudProvider,
        "mosheng": MoShangProvider,
    }
    cls = providers.get(provider_name)
    if cls is None:
        raise ValueError(f"Unknown provider: {provider_name}")
    return cls()
