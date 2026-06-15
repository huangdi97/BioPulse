"""Backward-compatible import redirects for Compliance V2 service."""

import warnings

from cloud.app.compliance.v2_service import ComplianceV, ComplianceV2Service

__all__ = ["ComplianceV", "ComplianceV2Service"]

warnings.warn(
    "cloud.app.services.compliance_v2_service is deprecated, use cloud.app.compliance.v2_service instead",
    DeprecationWarning,
    stacklevel=2,
)
