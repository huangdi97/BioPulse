"""Service-layer package for cloud app."""

from cloud.app.services.attribution_calc import AttributionCalcMixin, AttributionCheckMixin
from cloud.app.services.coach_ability import CoachAbility
from cloud.app.services.coach_gap import CoachGap
from cloud.app.services.intel_analyzer import IntelAnalyzerMixin, IntelCollectorMixin
from cloud.app.services.memory_namespace import MemoryNamespace
from cloud.app.services.memory_service import MemoryService
from cloud.app.services.network_crud import NetworkCrudMixin
from cloud.app.services.network_sync import NetworkSyncMixin
from cloud.app.services.utility_opt import UtilityOptMixin
from cloud.app.services.utility_score import UtilityScoreMixin
from shared.base_service import BaseService


class CausalAttributionService(AttributionCalcMixin, AttributionCheckMixin, BaseService):
    """因果归因服务，合并归因刷新、模拟与读取能力。"""


class CellNetworkService(NetworkCrudMixin, NetworkSyncMixin, BaseService):
    """Cell 网络服务，整合网络 CRUD 与节点同步能力。"""


class MemoryUtilityService(UtilityScoreMixin, UtilityOptMixin, BaseService):
    """记忆效用服务，组合评分计算与效用优化混入类。"""


class MarketIntelService(IntelCollectorMixin, IntelAnalyzerMixin, BaseService):
    """市场情报服务，组合情报采集与分析能力。"""


class CoachAssessor(BaseService, CoachAbility, CoachGap):
    """培训教练评估服务。"""


__all__ = [
    "BaseService",
    "MemoryNamespace",
    "MemoryService",
    "CausalAttributionService",
    "CellNetworkService",
    "CoachAssessor",
    "MarketIntelService",
    "MemoryUtilityService",
]
