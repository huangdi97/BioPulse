"""Backward-compatible import redirects for Compliance V2 service."""

from cloud.app.compliance.v2_service import ComplianceV, ComplianceV2Service

__all__ = ["ComplianceV", "ComplianceV2Service"]
