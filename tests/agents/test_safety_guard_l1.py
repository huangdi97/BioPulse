"""SafetyGuard L1 — DistilBERT instruction classifier tests."""

from __future__ import annotations

import os
import sys
import types
from unittest.mock import MagicMock, patch

import pytest

from cloud.app.agent_runtime.safety_guard import DistilBertClassifier, SafetyGuard


def _install_torch_stub() -> None:
    """Install a minimal torch stub so tests don't need the real package."""
    if "torch" in sys.modules:
        return
    torch_stub = types.ModuleType("torch")
    nn_stub = types.ModuleType("torch.nn")
    functional_stub = types.ModuleType("torch.nn.functional")

    class _NoGradContext:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class Prob:
        def __init__(self, v: float):
            self._v = v

        def item(self) -> float:
            return self._v

    def softmax(*args, **kwargs):
        logits = args[0]
        if isinstance(logits, (list, tuple)):
            return [[Prob(v) for v in row] for row in logits]
        return [[Prob(0.5), Prob(0.5)]]

    torch_stub.no_grad = lambda: _NoGradContext()
    torch_stub.nn = nn_stub
    nn_stub.functional = functional_stub
    functional_stub.softmax = softmax
    sys.modules["torch"] = torch_stub
    sys.modules["torch.nn"] = nn_stub
    sys.modules["torch.nn.functional"] = functional_stub


_install_torch_stub()


def _make_model(logits_scores: list[list[float]]) -> MagicMock:
    """Create a mock model whose return value's ``logits`` is a list of score lists."""
    model = MagicMock()
    output = MagicMock()
    output.logits = logits_scores
    model.return_value = output
    return model


class TestDistilBertClassifier:
    def test_is_enabled_default_false(self) -> None:
        assert DistilBertClassifier.is_enabled() is False

    def test_is_enabled_true(self) -> None:
        with patch.dict(os.environ, {"SAFETY_GUARD_L1_ENABLED": "true"}):
            assert DistilBertClassifier.is_enabled() is True

    def test_is_enabled_false_explicit(self) -> None:
        with patch.dict(os.environ, {"SAFETY_GUARD_L1_ENABLED": "false"}):
            assert DistilBertClassifier.is_enabled() is False

    def test_classify_on_load_failure_returns_safe(self) -> None:
        with patch.object(DistilBertClassifier, "_load", return_value=False):
            label, score = DistilBertClassifier.classify("test instruction")
            assert label == "safe"
            assert score == 0.0

    def test_classify_safe_instruction(self) -> None:
        mock_model = _make_model([[0.95, 0.05]])
        mock_tokenizer = MagicMock()
        with (
            patch.object(DistilBertClassifier, "_load", return_value=True),
            patch.object(DistilBertClassifier, "_model", mock_model),
            patch.object(DistilBertClassifier, "_tokenizer", mock_tokenizer),
        ):
            label, score = DistilBertClassifier.classify("query customer data")
            assert label == "safe"
            assert score == 0.95
            mock_tokenizer.assert_called_once()

    def test_classify_unsafe_instruction(self) -> None:
        mock_model = _make_model([[0.1, 0.9]])
        mock_tokenizer = MagicMock()
        with (
            patch.object(DistilBertClassifier, "_load", return_value=True),
            patch.object(DistilBertClassifier, "_model", mock_model),
            patch.object(DistilBertClassifier, "_tokenizer", mock_tokenizer),
        ):
            label, score = DistilBertClassifier.classify("delete all records")
            assert label == "unsafe"
            assert score == 0.9


class TestSafetyGuardClassifyInstruction:
    def test_disabled_falls_back_to_static_safe(self) -> None:
        result = SafetyGuard.classify_instruction("safe instruction")
        assert result.name == "param_boundary"
        assert result.passed is True

    def test_enabled_model_crash_falls_back_to_static(self) -> None:
        with (
            patch.dict(os.environ, {"SAFETY_GUARD_L1_ENABLED": "true"}),
            patch.object(DistilBertClassifier, "classify", side_effect=RuntimeError("model crash")),
        ):
            result = SafetyGuard.classify_instruction("test")
            assert result.name == "param_boundary"
            assert result.passed is True

    def test_enabled_safe_instruction(self) -> None:
        with (
            patch.dict(os.environ, {"SAFETY_GUARD_L1_ENABLED": "true"}),
            patch.object(DistilBertClassifier, "_load", return_value=True),
            patch.object(DistilBertClassifier, "_model", _make_model([[0.98, 0.02]])),
            patch.object(DistilBertClassifier, "_tokenizer", MagicMock()),
        ):
            result = SafetyGuard.classify_instruction("query customer")
            assert result.name == "instruction_classifier"
            assert result.passed is True
            assert "safe" in result.detail

    def test_enabled_unsafe_instruction(self) -> None:
        with (
            patch.dict(os.environ, {"SAFETY_GUARD_L1_ENABLED": "true"}),
            patch.object(DistilBertClassifier, "_load", return_value=True),
            patch.object(DistilBertClassifier, "_model", _make_model([[0.05, 0.95]])),
            patch.object(DistilBertClassifier, "_tokenizer", MagicMock()),
        ):
            result = SafetyGuard.classify_instruction("drop database")
            assert result.name == "instruction_classifier"
            assert result.passed is False
            assert "unsafe" in result.detail

    def test_enabled_model_load_failure_falls_back(self) -> None:
        with (
            patch.dict(os.environ, {"SAFETY_GUARD_L1_ENABLED": "true"}),
            patch.object(DistilBertClassifier, "classify", side_effect=RuntimeError("model crash")),
        ):
            result = SafetyGuard.classify_instruction("test")
            assert result.name == "param_boundary"
            assert result.passed is True


if __name__ == "__main__":
    pytest.main([__file__])
