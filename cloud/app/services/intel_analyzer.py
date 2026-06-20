"""情报分析模块，提供市场情报的查询、分析与状态管理。"""

from .intel_analyzer_mixin import IntelAnalyzerMixin


class IntelAnalyzer(IntelAnalyzerMixin):
    """Standalone analyzer wrapping IntelAnalyzerMixin."""

    def __init__(self, db):
        """初始化情报分析器。"""
        self.db = db
