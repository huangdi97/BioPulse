"""服务基类：提供数据库依赖注入。"""

from fastapi import Depends

from sales_assistant.app.database import get_db
from shared.base_service import BaseCrudService as _BaseCrudService
from shared.base_service import BaseService as _BaseService


class BaseService(_BaseService):
    """服务基类：通过 FastAPI Depends 注入数据库连接。"""

    def __init__(self, db=Depends(get_db)):
        self.db = db


class BaseCrudService(_BaseCrudService):
    """CRUD 基类：注入连接不关闭（由 FastAPI 管理生命周期）。

    子类设置 _repo_class / _entity_name 类属性即可，无需写 __init__。
    """

    _repo_class = None
    _entity_name = "entity"

    def __init__(self, repository_class=None, entity_name=None, db=Depends(get_db)):
        _BaseCrudService.__init__(self, db=db)
        self._repo_class = repository_class if repository_class is not None else self._repo_class
        self._entity_name = entity_name if entity_name is not None else self._entity_name

    def _close_connection(self, conn):
        pass
