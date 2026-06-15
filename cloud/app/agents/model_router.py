"""ModelRouter — 根据 agent_model.model_preference + 请求类型选择 provider/model。"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from cloud.app.agent_runtime.runtime_llm.config import get_fallback_chain
from cloud.app.config.provider_config import ProviderType

logger = logging.getLogger(__name__)

__all__ = ["RouteResult", "ModelRouter"]

RequestType = Literal["chat", "asr", "tts"]

_REQUEST_TYPE_MAP: dict[RequestType, ProviderType] = {
    "chat": ProviderType.LLM,
    "asr": ProviderType.ASR,
    "tts": ProviderType.TTS,
}

_DEFAULT_MAP: dict[ProviderType, dict[str, str]] = {
    ProviderType.LLM: {"provider": "deepseek", "model": "deepseek-chat", "mode": "api"},
    ProviderType.ASR: {"provider": "whisper", "model": "whisper-1", "mode": "api"},
    ProviderType.TTS: {"provider": "openai", "model": "tts-1", "mode": "api"},
}


@dataclass(frozen=True)
class RouteResult:
    provider: str
    model: str
    mode: str


class ModelRouter:
    """根据 agent 的 model_preference 和请求类型选择 provider/model。

    fallback 链: preferred → default → fallback
    """

    @staticmethod
    def select(
        agent_model: object,
        request_type: RequestType = "chat",
        context: object | None = None,
    ) -> RouteResult:
        provider_type = _REQUEST_TYPE_MAP.get(request_type, ProviderType.LLM)
        preference = getattr(agent_model, "model_preference", "") or ""

        preferred = ModelRouter._parse_preference(preference, provider_type)
        if preferred is not None:
            return preferred

        default = _DEFAULT_MAP.get(provider_type)
        if default is not None:
            return RouteResult(**default)

        return ModelRouter._first_fallback()

    @staticmethod
    def _parse_preference(preference: str, provider_type: ProviderType) -> RouteResult | None:
        if not preference:
            return None
        parts = preference.split("/", 1)
        provider = parts[0].strip()
        model = parts[1].strip() if len(parts) > 1 else provider
        mode = "api"
        return RouteResult(provider=provider, model=model, mode=mode)

    @staticmethod
    def _first_fallback() -> RouteResult:
        chain = get_fallback_chain()
        entry = chain[0] if chain else {}
        return RouteResult(
            provider=entry["provider"],
            model=entry["model"],
            mode=entry["mode"],
        )
