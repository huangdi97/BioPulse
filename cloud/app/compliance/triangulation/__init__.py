# DEPRECATED: 请使用 cloud.app.compliance.holographic_audit 模块

"""Holographic audit checks (DEPRECATED — use holographic_audit)."""

from .decision import TriangulationFinding, TriangulationResult
from .engine import TriangulationEngine

__all__ = ["TriangulationEngine", "TriangulationFinding", "TriangulationResult"]
