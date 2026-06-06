"""服务层基类模块。"""

from fastapi import Depends

from sales_coach.app.database import get_db


class BaseService:
    """服务层基类，提供数据库依赖注入。"""

    def __init__(self, db=Depends(get_db)):
        self.db = db
