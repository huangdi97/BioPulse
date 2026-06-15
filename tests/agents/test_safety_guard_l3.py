"""SafetyGuard L3 — LLM side-effect prediction tests."""

from __future__ import annotations

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cloud.app.agent_runtime.safety_guard import SafetyGuard


class TestSafetyGuardPredictSideEffectLLM:
    def _run(self, coro):
        return asyncio.run(coro)

    def test_disabled_falls_back_to_static(self) -> None:
        llm_service = MagicMock()
        with patch.dict(os.environ, {"SAFETY_GUARD_L3_ENABLED": "false"}, clear=True):
            result = self._run(SafetyGuard.predict_side_effect_llm("unknown_tool", {"key": "val"}, llm_service))
        assert result.name == "side_effect"
        assert result.passed is True
        llm_service.generate.assert_not_called()

    def test_enabled_llm_returns_low_risk(self) -> None:
        llm_service = AsyncMock()
        llm_service.generate.return_value = '{"risk_level": "low", "effects": ["writes audit log"], "recommendation": "允许"}'
        with patch.dict(os.environ, {"SAFETY_GUARD_L3_ENABLED": "true"}, clear=True):
            result = self._run(SafetyGuard.predict_side_effect_llm("submit_interaction", {"hcp_id": 123}, llm_service))
        assert result.name == "side_effect_llm"
        assert result.passed is True
        assert "low" in result.detail

    def test_enabled_llm_returns_high_risk_blocked(self) -> None:
        llm_service = AsyncMock()
        llm_service.generate.return_value = '{"risk_level": "high", "effects": ["暂停费用发放", "通知合规官"], "recommendation": "禁止"}'
        with patch.dict(os.environ, {"SAFETY_GUARD_L3_ENABLED": "true"}, clear=True):
            result = self._run(SafetyGuard.predict_side_effect_llm("trigger_red_light", {"amount": 50000}, llm_service))
        assert result.name == "side_effect_llm"
        assert result.passed is False

    def test_llm_failure_falls_back_to_static(self) -> None:
        llm_service = AsyncMock()
        llm_service.generate.side_effect = RuntimeError("LLM unavailable")
        with patch.dict(os.environ, {"SAFETY_GUARD_L3_ENABLED": "true"}, clear=True):
            result = self._run(SafetyGuard.predict_side_effect_llm("submit_interaction", {"hcp_id": 123}, llm_service))
        assert result.name == "side_effect"
        assert result.passed is True

    def test_llm_invalid_json_falls_back_to_static(self) -> None:
        llm_service = AsyncMock()
        llm_service.generate.return_value = "not json at all"
        with patch.dict(os.environ, {"SAFETY_GUARD_L3_ENABLED": "true"}, clear=True):
            result = self._run(SafetyGuard.predict_side_effect_llm("submit_interaction", {"hcp_id": 123}, llm_service))
        assert result.name == "side_effect"
        assert result.passed is True


if __name__ == "__main__":
    pytest.main([__file__])
