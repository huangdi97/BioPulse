"""服务层基类模块。"""

from assistant.app.database import DB_PATH
from shared.base_service import BaseCrudService as _BaseCrudService
from shared.base_service import BaseService as _BaseService


class BaseService(_BaseService):
    """服务基类，每个方法独立管理数据库连接。"""

    def _connection(self):
        return self._connect(DB_PATH)


class BaseCrudService(_BaseCrudService, BaseService):
    """CRUD 基类，继承 shared.BaseCrudService 并使用 assistant 的数据库连接。"""

    pass
