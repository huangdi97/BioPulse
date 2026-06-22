"""Backward-compatible re-export — delegates to holographic_audit module."""

from cloud.app.compliance.holographic_audit import HolographicAuditEngine, HolographicFinding, HolographicResult

__all__ = ["HolographicAuditEngine", "HolographicFinding", "HolographicResult"]

# DEPRECATED aliases
TriangulationEngine = HolographicAuditEngine
TriangulationFinding = HolographicFinding
TriangulationResult = HolographicResult
