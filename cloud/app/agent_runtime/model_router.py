"""ModelRouter — 将 Agent identity 的 model_preference 映射到 LLM 配置。"""

from cloud.app.agent_runtime.models import ModelPreference
from cloud.app.agent_runtime.runtime_llm import RuntimeLLM


class ModelRouter:
    """包装 RuntimeLLM，按 model_preference 注入 temperature。"""

    def __init__(self, preference: ModelPreference | None = None):
        self.preference = preference
        self._llm = RuntimeLLM()

    @property
    def temperature(self) -> float:
        return self.preference.temperature if self.preference else 0.7

    def build_request_body(self, messages: list[dict]) -> dict:
        """构建 LLM 请求体，注入 temperature。"""
        body = {
            "model": self.preference.model if self.preference else "deepseek-v4-flash",
            "messages": messages,
            "temperature": self.temperature,
        }
        return body

    def call(self, messages: list[dict]) -> dict:
        """调用 LLM 并返回响应。"""
        body = self.build_request_body(messages)
        return self._llm._raw_llm_call(body)
