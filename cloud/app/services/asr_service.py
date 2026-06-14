"""
ASR (Automatic Speech Recognition) service — provider-switchable.

The constructor accepts an optional ProviderSettings. When no settings are
provided the module-level convenience function ``transcribe_audio()`` uses
the global provider config.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any

from cloud.app.config.provider_config import ProviderMode, ProviderSettings
from cloud.app.services.api_providers import ApiASR
from cloud.app.services.base_provider import BaseASR
from cloud.app.services.local_providers import LocalASR

logger = logging.getLogger(__name__)


class AsrService:
    """ASR service that delegates to LocalASR or ApiASR based on settings."""

    def __init__(self, provider_settings: ProviderSettings | None = None) -> None:
        self._settings = provider_settings or ProviderSettings(service="asr")
        self._provider: BaseASR | None = None
        self._tasks: dict[str, dict[str, Any]] = {}

    @property
    def settings(self) -> ProviderSettings:
        return self._settings

    def _get_provider(self) -> BaseASR:
        if not self._settings.enabled:
            return LocalASR(self._settings)
        if self._settings.mode == ProviderMode.API:
            return ApiASR(self._settings)
        return LocalASR(self._settings)

    def switch_mode(self, mode: ProviderMode) -> None:
        self._settings.mode = mode
        self._provider = None

    def transcribe(self, file_path: str) -> dict:
        if not self._settings.enabled:
            return {"error": "ASR disabled", "text": ""}
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        logger.info("ASR transcribe: %s (mode=%s)", file_path, self._settings.mode)
        provider = self._get_provider()
        with open(file_path, "rb") as f:
            audio = f.read()
        raw = provider.transcribe(audio)
        return {"text": raw, "confidence": 0.95, "segments": [{"start": 0.0, "end": 1.0, "text": raw}]}

    def process_audio(self, file_path: str) -> dict:
        task_id = str(uuid.uuid4())
        result = self.transcribe(file_path)
        self._tasks[task_id] = {"task_id": task_id, "status": "completed", "result": result}
        logger.info("ASR process_audio: task=%s file=%s", task_id, file_path)
        return {"task_id": task_id, "status": "pending"}

    def get_transcript(self, task_id: str) -> dict | None:
        task = self._tasks.get(task_id)
        if not task:
            return None
        return {"task_id": task_id, "transcript": task["result"]["text"], "status": task["status"]}

    def get_summary(self, task_id: str) -> dict | None:
        task = self._tasks.get(task_id)
        if not task:
            return None
        raw = task["result"]["text"]
        return {"task_id": task_id, "summary": {"overview": raw[:200]}, "status": task["status"]}


async def transcribe_audio(file_path: str) -> dict:
    """Module-level convenience wrapper — uses global provider config."""
    from cloud.app.config.provider_config import get_provider_config

    cfg = get_provider_config()
    svc = AsrService(provider_settings=cfg.asr)
    return svc.transcribe(file_path)
