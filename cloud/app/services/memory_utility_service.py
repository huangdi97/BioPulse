"""记忆效用服务，整合评分与效用优化能力。"""

from cloud.app.services.base import BaseService
from cloud.app.services.utility_opt import UtilityOptMixin
from cloud.app.services.utility_score import UtilityScoreMixin


class MemoryUtilityService(UtilityScoreMixin, UtilityOptMixin, BaseService):
    """记忆效用服务，组合评分计算与效用优化混入类。"""

    pass
