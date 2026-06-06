"""评分与统计报表数据仓库。"""

import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

from shared.columns import (
    TABLE_PAPER_INTEGRITY_COLS,
    TABLE_TREND_ANALYSIS_COLS,
)
from shared.repository import BaseRepository


class StatsRepository:
    """统计报表数据仓库。"""

    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self.table = "opportunity"

    def _build_where(
        self,
        conditions: list,
        params: list,
        start_date: str | None,
        end_date: str | None,
    ) -> None:
        if start_date:
            conditions.append("created_at >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date)

    def _where_clause(self, start_date: str | None, end_date: str | None) -> tuple[str, list]:
        conditions = ["is_active = 1"]
        params: list = []
        self._build_where(conditions, params, start_date, end_date)
        return "WHERE " + " AND ".join(conditions), params

    def get_totals(self, start_date: str | None = None, end_date: str | None = None):
        where, params = self._where_clause(start_date, end_date)
        row = self.db.execute(
            f"SELECT COUNT(*), COALESCE(SUM(estimated_value), 0) FROM {self.table} {where}",
            params,
        ).fetchone()
        return row[0], row[1]

    def get_by_stage(self, start_date: str | None = None, end_date: str | None = None) -> List[sqlite3.Row]:
        where, params = self._where_clause(start_date, end_date)
        return self.db.execute(
            f"SELECT stage, COUNT(*), COALESCE(SUM(estimated_value), 0) FROM {self.table} {where} GROUP BY stage",
            params,
        ).fetchall()

    def get_by_product(self, start_date: str | None = None, end_date: str | None = None) -> List[sqlite3.Row]:
        where, params = self._where_clause(start_date, end_date)
        return self.db.execute(
            f"SELECT product, COUNT(*), COALESCE(SUM(estimated_value), 0) FROM {self.table} {where} AND product IS NOT NULL GROUP BY product",
            params,
        ).fetchall()


class PaperIntegrityRepository(BaseRepository):
    """论文诚信数据仓库。"""

    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "paper_integrity", TABLE_PAPER_INTEGRITY_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM paper_integrity
               WHERE is_active = 1
                 AND (title LIKE ? OR pubmed_id LIKE ? OR doi LIKE ? OR concerns LIKE ?)
               ORDER BY updated_at DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()

    def soft_delete(self, row_id: int) -> None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute(
            "UPDATE paper_integrity SET is_active = 0, updated_at = ? WHERE id = ?",
            (now, row_id),
        )
        self.db.commit()

    def list_by_user(self, user_id: int) -> List[sqlite3.Row]:
        return self.list_all(
            conditions=["created_by = ?", "is_active = 1"],
            params=[user_id],
            order_by="updated_at DESC",
        )

    def get_by_pubmed_id(self, pubmed_id: str) -> Optional[sqlite3.Row]:
        return self.db.execute(
            "SELECT * FROM paper_integrity WHERE pubmed_id = ? AND is_active = 1",
            (pubmed_id,),
        ).fetchone()


class TrendAnalysisRepository(BaseRepository):
    """趋势分析数据仓库。"""

    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "trend_analysis", TABLE_TREND_ANALYSIS_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM trend_analysis
               WHERE topic LIKE ? OR result LIKE ? OR analysis_type LIKE ?
               ORDER BY analyzed_at DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()

    def soft_delete(self, row_id: int) -> None:
        self.db.execute("DELETE FROM trend_analysis WHERE id = ?", (row_id,))
        self.db.commit()

    def list_by_user(self, user_id: int) -> List[sqlite3.Row]:
        return self.list_all(
            conditions=["created_by = ?"],
            params=[user_id],
            order_by="analyzed_at DESC",
        )
