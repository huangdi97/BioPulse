"""服务层基类模块。"""

from fastapi import Depends

from assistant.app.database import get_db


class BaseService:
    """服务基类，通过 FastAPI 依赖注入获取数据库连接。"""

    def __init__(self, db=Depends(get_db)):
        self.db = db
