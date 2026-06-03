from cloud.shared.columns import (
    TABLE_CONTENTS_COLS,
    TABLE_RECOMMENDATIONS_COLS,
    TABLE_SUPPLY_CHAIN_ITEMS_COLS,
)
from cloud.shared.repository import BaseRepository


class RecommendationsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "recommendations", TABLE_RECOMMENDATIONS_COLS)

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]

    def count_clicked(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE clicked=1").fetchone()[0]

    def count_dismissed(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE dismissed=1").fetchone()[0]

    def count_by_rec_type(self):
        rows = self.db.execute(
            f"SELECT rec_type, COUNT(*) as cnt FROM {self.table_name} GROUP BY rec_type ORDER BY cnt DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def list_filtered(
        self,
        user_id=None,
        rec_type=None,
        clicked=None,
        dismissed=None,
        limit=50,
        offset=0,
    ):
        conditions, params = [], []
        if user_id is not None:
            conditions.append("user_id=?")
            params.append(user_id)
        if rec_type is not None:
            conditions.append("rec_type=?")
            params.append(rec_type)
        if clicked is not None:
            conditions.append("clicked=?")
            params.append(clicked)
        if dismissed is not None:
            conditions.append("dismissed=?")
            params.append(dismissed)
        return self.paginate(
            page=1,
            page_size=limit,
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )

    def mark_clicked(self, rec_id: int) -> bool:
        cursor = self.db.execute(f"UPDATE {self.table_name} SET clicked=1 WHERE id=?", (rec_id,))
        self.db.commit()
        return cursor.rowcount > 0

    def mark_dismissed(self, rec_id: int) -> bool:
        cursor = self.db.execute(f"UPDATE {self.table_name} SET dismissed=1 WHERE id=?", (rec_id,))
        self.db.commit()
        return cursor.rowcount > 0


class ContentsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "contents", TABLE_CONTENTS_COLS)


class SupplyChainItemsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "supply_chain_items", TABLE_SUPPLY_CHAIN_ITEMS_COLS)

    def list_filtered(self, category=None, status=None):
        conditions, params = [], []
        if category:
            conditions.append("category=?")
            params.append(category)
        if status:
            conditions.append("status=?")
            params.append(status)
        placeholders = ", ".join(self.cols)
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name}{where} ORDER BY created_at DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]
