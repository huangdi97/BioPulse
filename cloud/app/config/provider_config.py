"""Provider configuration definitions for BioPulse AI services."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum


class ProviderType(str, Enum):
    LLM = "llm"
    ASR = "asr"
    TTS = "tts"
    PUSH = "push"


class ProviderMode(str, Enum):
    LOCAL = "local"
    API = "api"


@dataclass
class ProviderSettings:
    service: str
    enabled: bool = True
    mode: ProviderMode = ProviderMode.LOCAL
    local_endpoint: str | None = None
    api_key: str | None = None
    api_endpoint: str | None = None
    model_name: str | None = None
    timeout_seconds: int = 30
    max_retries: int = 3


@dataclass
class ProviderConfig:
    llm: ProviderSettings = field(
        default_factory=lambda: ProviderSettings(
            service="llm",
            model_name="local-llm",
        )
    )
    asr: ProviderSettings = field(
        default_factory=lambda: ProviderSettings(
            service="asr",
            model_name="local-whisper",
        )
    )
    tts: ProviderSettings = field(
        default_factory=lambda: ProviderSettings(
            service="tts",
            model_name="local-piper",
        )
    )
    push: ProviderSettings = field(
        default_factory=lambda: ProviderSettings(
            service="push",
            model_name="local-log",
        )
    )


_ENV_MODE_MAP: dict[str, ProviderMode] = {
    "local": ProviderMode.LOCAL,
    "api": ProviderMode.API,
}


def _resolve_mode(env_var: str, default: ProviderMode) -> ProviderMode:
    raw = os.environ.get(env_var)
    if raw:
        normalized = raw.strip().lower()
        return _ENV_MODE_MAP.get(normalized, default)
    return default


def get_provider_config() -> ProviderConfig:
    cfg = ProviderConfig()

    cfg.llm.mode = _resolve_mode("PROVIDER_LLM_MODE", cfg.llm.mode)
    cfg.asr.mode = _resolve_mode("PROVIDER_ASR_MODE", cfg.asr.mode)
    cfg.tts.mode = _resolve_mode("PROVIDER_TTS_MODE", cfg.tts.mode)
    cfg.push.mode = _resolve_mode("PROVIDER_PUSH_MODE", cfg.push.mode)

    cfg.llm.api_endpoint = os.environ.get("PROVIDER_LLM_ENDPOINT") or cfg.llm.api_endpoint
    cfg.llm.api_key = os.environ.get("PROVIDER_LLM_API_KEY") or cfg.llm.api_key
    cfg.llm.model_name = os.environ.get("PROVIDER_LLM_MODEL") or cfg.llm.model_name
    cfg.asr.api_endpoint = os.environ.get("PROVIDER_ASR_ENDPOINT") or cfg.asr.api_endpoint
    cfg.asr.api_key = os.environ.get("PROVIDER_ASR_API_KEY") or cfg.asr.api_key
    cfg.tts.api_endpoint = os.environ.get("PROVIDER_TTS_ENDPOINT") or cfg.tts.api_endpoint
    cfg.tts.api_key = os.environ.get("PROVIDER_TTS_API_KEY") or cfg.tts.api_key
    cfg.push.api_endpoint = os.environ.get("PROVIDER_PUSH_ENDPOINT") or cfg.push.api_endpoint
    cfg.push.api_key = os.environ.get("PROVIDER_PUSH_API_KEY") or cfg.push.api_key

    return cfg