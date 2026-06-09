"""Generic SQLite/PostgreSQL database base class for all service ends."""

import json
import logging
import os
import sqlite3
import time
from typing import Generator

from shared.db import PGCompatConnection

logger = logging.getLogger(__name__)


class SQLiteDatabase:
    """Base class for SQLite/PostgreSQL database management.

    Subclasses override init_db() to add service-specific schema, seeds,
    and migrations. Module-level get_db() / init_db() delegate to an
    instance to keep backward-compatible import paths.
    """

    def __init__(
        self,
        db_path: str,
        database_url: str | None = None,
        schema_sql: str | None = None,
        pg_schema_sql: str | None = None,
    ) -> None:
        self.db_path = db_path
        self.database_url = database_url or ""
        self.schema_sql = schema_sql or ""
        self.pg_schema_sql = pg_schema_sql or ""

    def get_db(self) -> Generator:
        if self.database_url and (self.database_url.startswith("postgresql://") or self.database_url.startswith("postgres://")):
            import psycopg2

            conn = PGCompatConnection(psycopg2.connect(self.database_url))
            try:
                yield conn
            finally:
                conn.close()
        else:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()

    def get_db_sqlite_only(self) -> Generator:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self) -> None:
        if self.database_url and (self.database_url.startswith("postgresql://") or self.database_url.startswith("postgres://")):
            import psycopg2

            conn = PGCompatConnection(psycopg2.connect(self.database_url))
            try:
                if self.pg_schema_sql:
                    conn.executescript(self.pg_schema_sql)
                conn.commit()
            finally:
                conn.close()
        else:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            try:
                if self.schema_sql:
                    conn.executescript(self.schema_sql)
                self._run_migrations(conn)
                conn.commit()
            finally:
                conn.close()
            self._post_init_migrations()

    def _run_migrations(self, conn: sqlite3.Connection) -> None:
        """Override in subclasses to add ALTER TABLE / CREATE INDEX migrations."""

    def _post_init_migrations(self) -> None:
        """Override in subclasses to run SQLite-only migrations after init_db."""

    def _ensure_columns(
        self,
        conn: sqlite3.Connection,
        table: str,
        columns: list[tuple[str, str]],
    ) -> None:
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for col_name, col_def in columns:
            if col_name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")


class SQLiteCache:
    """Generic API response cache backed by SQLite."""

    def __init__(self, db_path: str, default_ttl: int = 600) -> None:
        self.db_path = db_path
        self.default_ttl = default_ttl

    def init_cache_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            f"CREATE TABLE IF NOT EXISTS api_cache ("
            f"cache_key TEXT PRIMARY KEY, "
            f"response TEXT, "
            f"cached_at REAL, "
            f"ttl INTEGER DEFAULT {self.default_ttl}"
            f")"
        )
        conn.commit()
        conn.close()

    def get_cache(self, key: str) -> dict | None:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT response, cached_at, ttl FROM api_cache WHERE cache_key=?",
            (key,),
        ).fetchone()
        conn.close()
        if row:
            if time.time() - row[1] < row[2]:
                return json.loads(row[0])
        return None

    def set_cache(self, key: str, data: dict, ttl: int | None = None) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO api_cache (cache_key, response, cached_at, ttl) VALUES (?, ?, ?, ?)",
            (key, json.dumps(data, default=str), time.time(), ttl if ttl is not None else self.default_ttl),
        )
        conn.commit()
        conn.close()
