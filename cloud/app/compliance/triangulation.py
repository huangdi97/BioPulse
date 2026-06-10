"""Backward-compatible re-export for triangulation module."""
from cloud.app.compliance.triangulation.decision import TriangulationFinding, TriangulationResult
from cloud.app.compliance.triangulation.engine import TriangulationEngine

__all__ = ["TriangulationEngine", "TriangulationFinding", "TriangulationResult"]
