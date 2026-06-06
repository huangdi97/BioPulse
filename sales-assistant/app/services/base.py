"""服务基类：提供数据库依赖注入。"""

from fastapi import Depends

from sales_assistant.app.database import get_db


class BaseService:
    """服务基类：通过 FastAPI Depends 注入数据库连接。"""

    def __init__(self, db=Depends(get_db)):
        self.db = db
