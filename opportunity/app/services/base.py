from fastapi import Depends

from opportunity.app.database import get_db


class BaseService:
    def __init__(self, db=Depends(get_db)):
        self.db = db
