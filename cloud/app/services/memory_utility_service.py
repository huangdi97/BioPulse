from cloud.app.services.base import BaseService
from cloud.app.services.utility_opt import UtilityOptMixin
from cloud.app.services.utility_score import UtilityScoreMixin


class MemoryUtilityService(UtilityScoreMixin, UtilityOptMixin, BaseService):
    pass
