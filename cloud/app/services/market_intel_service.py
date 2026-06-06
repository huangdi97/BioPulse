"""市场情报服务，整合情报采集与分析功能。"""

from cloud.app.services.base import BaseService
from cloud.app.services.intel_analyzer import IntelAnalyzerMixin
from cloud.app.services.intel_collector import IntelCollectorMixin


class MarketIntelService(IntelCollectorMixin, IntelAnalyzerMixin, BaseService):
    """市场情报服务，组合情报采集与分析能力。"""

    pass
