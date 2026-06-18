import logging
import re

from shared.config import settings
from shared.pg_row import PGRow  # noqa: F401

logger = logging.getLogger(__name__)

DATABASE_URL = settings.database_url


def is_sqlite() -> bool:
    return DATABASE_URL.startswith("sqlite://")


def get_db_type() -> str:
    return "sqlite" if is_sqlite() else "postgresql"


def _replace_insert_or_replace(m: re.Match) -> str:
    """将 INSERT OR REPLACE INTO t (cols) VALUES (vals) 转换为 PG 兼容格式。
    首列作为冲突列（settings 模式），也可覆盖特定表名映射。
    """
    table = m.group(1)
    cols = [c.strip() for c in m.group(2).split(",")]
    vals = m.group(3)
    conflict_col = cols[0]
    set_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols[1:]) if len(cols) > 1 else ""
    return f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({vals}) ON CONFLICT ({conflict_col}) DO UPDATE SET {set_clause}"


class PGCompatCursor:
    def __init__(self, cur, description=None):
        self._cur = cur
        self._desc = description
        self.lastrowid = None

    def execute(self, sql, params=None):
        # --- SQLite -> PG SQL 兼容转换 ---
        sql = sql.replace("?", "%s")
        # datetime('now') -> CURRENT_TIMESTAMP
        sql = re.sub(r"""(?i)\bdatetime\s*\(\s*'now'\s*\)""", "CURRENT_TIMESTAMP", sql)
        sql = re.sub(r"""(?i)\bdatetime\s*\(\s*"now"\s*,\s*"localtime"\s*\)""", "CURRENT_TIMESTAMP", sql)
        # rowid -> id（SQLite 中 INTEGER PRIMARY KEY 即 rowid 别名）
        sql = re.sub(r"\browid\b", "id", sql, flags=re.IGNORECASE)
        # last_insert_rowid() -> LASTVAL()
        sql = re.sub(r"\blast_insert_rowid\s*\(\s*\)", "LASTVAL()", sql, flags=re.IGNORECASE)
        # INSERT OR REPLACE -> INSERT ... ON CONFLICT DO UPDATE
        sql = re.sub(
            r"(?i)\bINSERT\s+OR\s+REPLACE\s+INTO\s+(\w+)\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)",
            _replace_insert_or_replace,
            sql,
        )

        self._cur.execute(sql, params)
        self._desc = self._cur.description
        # 捕获 INSERT 后的 lastrowid（psycopg 不自动设置，用 LASTVAL() 取序列值）
        if self.lastrowid is None and sql.strip().upper().startswith("INSERT"):
            try:
                self._cur.execute("SELECT LASTVAL()")
                self.lastrowid = self._cur.fetchone()[0]
            except Exception:
                pass
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
