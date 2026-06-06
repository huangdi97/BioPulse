from fastapi import Depends

from opportunity.app.database import get_db

"""服务层基类，提供 FastAPI Depends 注入的数据库会话。"""


class BaseService:
    """服务基类，通过 FastAPI Depends 注入数据库会话供子类使用。"""

    def __init__(self, db=Depends(get_db)):
        self.db = db
