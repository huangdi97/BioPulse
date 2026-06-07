import logging

from shared.config import settings
from shared.pg_row import PGRow  # noqa: F401

logger = logging.getLogger(__name__)

DATABASE_URL = settings.DATABASE_URL


def is_sqlite() -> bool:
    return DATABASE_URL.startswith("sqlite://")


def get_db_type() -> str:
    return "sqlite" if is_sqlite() else "postgresql"


class PGCompatCursor:
    def __init__(self, cur, description=None):
        self._cur = cur
        self._desc = description
        self.lastrowid = None

    def execute(self, sql, params=None):
        sql = sql.replace("?", "%s")
        self._cur.execute(sql, params)
        self._desc = self._cur.description
        return self

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        if self._desc is None:
            return PGRow(row) if isinstance(row, dict) else row
        cols = [d[0] for d in self._desc] if self._desc else []
        if isinstance(row, (list, tuple)):
            return PGRow(zip(cols, row))
        return PGRow(row)

    def fetchall(self):
        rows = self._cur.fetchall()
        if not rows:
            return []
        if self._desc is None:
            result = []
            for row in rows:
                if isinstance(row, dict):
                    result.append(PGRow(row))
                else:
                    result.append(row)
            return result
        cols = [d[0] for d in self._desc] if self._desc else []
        result = []
        for row in rows:
            if isinstance(row, (list, tuple)):
                result.append(PGRow(zip(cols, row)))
            else:
                result.append(PGRow(row))
        return result

    @property
    def rowcount(self):
        return self._cur.rowcount

    def close(self):
        self._cur.close()


class PGCompatConnection:
    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=None):
        cur = self._conn.cursor()
        pgc = PGCompatCursor(cur)
        pgc.execute(sql, params)
        return pgc

    def commit(self):
        self._conn.commit()

    def cursor(self):
        return self._conn.cursor()

    def close(self):
        self._conn.close()

    def executescript(self, script: str) -> None:
        """Execute multi-statement SQL script (compatible with sqlite3.executescript)."""
        cur = self._conn.cursor()
        for statement in script.split(";"):
            stmt = statement.strip()
            if stmt:
                try:
                    cur.execute(stmt)
                except Exception as e:
                    logger.warning(f"[PGCompatConnection] Skipping statement: {e}")
        cur.close()
        self._conn.commit()
