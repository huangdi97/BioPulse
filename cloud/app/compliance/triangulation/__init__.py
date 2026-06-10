"""Triangulation checks across expense, visit, and distribution data."""

from .decision import TriangulationFinding, TriangulationResult
from .engine import TriangulationEngine

__all__ = ["TriangulationEngine", "TriangulationFinding", "TriangulationResult"]
