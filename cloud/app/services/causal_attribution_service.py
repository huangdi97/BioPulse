"""因果归因服务，组合归因计算与归因查询两个混入类。"""

from cloud.app.services.attribution_calc import AttributionCalcMixin
from cloud.app.services.attribution_check import AttributionCheckMixin
from cloud.app.services.base import BaseService


class CausalAttributionService(AttributionCalcMixin, AttributionCheckMixin, BaseService):
    """因果归因服务，合并归因刷新、模拟与读取能力。"""

    pass
