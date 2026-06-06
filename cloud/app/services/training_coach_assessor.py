"""培训教练评估服务用于评估用户能力水平。"""

from cloud.app.services.base import BaseService
from cloud.app.services.coach_ability import CoachAbility
from cloud.app.services.coach_gap import CoachGap


class CoachAssessor(BaseService, CoachAbility, CoachGap):
    pass
