from cloud.app.services.base import BaseService
from cloud.app.services.intel_analyzer import IntelAnalyzerMixin
from cloud.app.services.intel_collector import IntelCollectorMixin


class MarketIntelService(IntelCollectorMixin, IntelAnalyzerMixin, BaseService):
    pass
