"""Backward-compatible import redirects for compliance management services."""

import warnings

from cloud.app.compliance.service import ComplianceService

__all__ = ["ComplianceService"]

warnings.warn(
    "cloud.app.services.compliance_service is deprecated, use cloud.app.compliance.service instead",
    DeprecationWarning,
    stacklevel=2,
)
