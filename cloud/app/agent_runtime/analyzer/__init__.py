"""L4 Meta-Cognitive: Analyzer — composite facade for failure classification and hypothesis verification."""

from cloud.app.agent_runtime.analyzer.classifier import FailureClassifier, call_llm, extract_json
from cloud.app.agent_runtime.analyzer.hypothesis import HypothesisEngine
from cloud.app.agent_runtime.analyzer.models import Analysis, Hypothesis, RootCauseNarrative, VerificationPlan, VerificationResult


class Analyzer(FailureClassifier, HypothesisEngine):
    """Combined analyzer — failure classification + hypothesis verification."""


__all__ = [
    "Analysis",
    "Analyzer",
    "FailureClassifier",
    "Hypothesis",
    "HypothesisEngine",
    "RootCauseNarrative",
    "VerificationPlan",
    "VerificationResult",
    "call_llm",
    "extract_json",
]
