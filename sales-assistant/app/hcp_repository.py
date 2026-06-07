import sqlite3
from typing import List

from shared.columns import (
    TABLE_HCP_PRODUCT_RELATION_COLS,
    TABLE_PRODUCT_COLS,
    TABLE_SALES_ASSISTANT_HCP_COLS,
    TABLE_VISIT_HCP_COLS,
)
from shared.repository import BaseRepository


class HcpRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "hcp", TABLE_SALES_ASSISTANT_HCP_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM hcp
               WHERE is_active = 1
                 AND (name LIKE ? OR hospital LIKE ? OR department LIKE ?
                      OR specialty LIKE ? OR city LIKE ?)
               ORDER BY updated_at DESC LIMIT ?""",
            (
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                limit,
            ),
        ).fetchall()


class ProductRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "product", TABLE_PRODUCT_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM product
               WHERE is_active = 1
                 AND (name LIKE ? OR category LIKE ? OR specification LIKE ?
                      OR company LIKE ?)
               ORDER BY updated_at DESC LIMIT ?""",
            (
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                limit,
            ),
        ).fetchall()


class RelationRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "hcp_product_relation", TABLE_HCP_PRODUCT_RELATION_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM hcp_product_relation
               WHERE is_active = 1
                 AND (relation_type LIKE ? OR strength LIKE ? OR notes LIKE ?)
               ORDER BY updated_at DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()


class VisitRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "visit_hcp", TABLE_VISIT_HCP_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM visit_hcp
               WHERE products_discussed LIKE ? OR hcp_feedback LIKE ?
               ORDER BY created_at DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()
