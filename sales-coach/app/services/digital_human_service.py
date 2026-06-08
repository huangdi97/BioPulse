"""数字人服务模块，管理数字人导练会话的创建、对话与评估。"""

from fastapi import Depends

from sales_coach.app.database import get_db
from sales_coach.app.services.base import BaseService
from sales_coach.app.services.dh_dialog import DHDialogMixin
from sales_coach.app.services.dh_profile import DHProfileMixin
from sales_coach.app.services.digital_human_provider import get_provider
from shared.config import settings


class DigitalHumanService(DHDialogMixin, DHProfileMixin, BaseService):
    """DigitalHuman 服务类。"""

    def __init__(self, db=Depends(get_db)):
        super().__init__(db)
        self._provider = get_provider(settings.digital_human_provider)
