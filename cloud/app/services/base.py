"""服务基类模块。"""

from fastapi import Depends

from cloud.app.database import get_db


class BaseService:
    """所有服务类的基类，提供数据库访问依赖注入。"""

    def __init__(self, db=Depends(get_db)):
        self.db = db
