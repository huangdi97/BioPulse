"""Backward-compatible import redirects for compliance engine services."""

import warnings

from cloud.app.compliance.engine import ComplianceEnforcer, ComplianceEngine
from cloud.app.compliance.research_enforcer import ResearchComplianceEnforcer
from cloud.app.compliance.strategy_service import ComplianceStrategyService

__all__ = ["ComplianceEnforcer", "ComplianceEngine", "ComplianceStrategyService", "ResearchComplianceEnforcer"]

warnings.warn(
    "cloud.app.services.compliance_engine is deprecated, use cloud.app.compliance.engine instead",
    DeprecationWarning,
    stacklevel=2,
)
