"""Data persistence for crawled competitor data — dual-store (time-series + relational)."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Optional


class CrawlerStorage:
    """Dual-store persistence for crawler data.

    Time-series store holds price/history snapshots.
    Relational store holds metadata, source configs, and crawl logs.
    """

    def __init__(self, db_path: str = ":memory:"):
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS crawler_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                url_template TEXT NOT NULL,
                crawl_frequency_minutes INTEGER NOT NULL DEFAULT 1440,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS crawler_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL,
                keyword TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT DEFAULT '',
                summary TEXT DEFAULT '',
                author TEXT DEFAULT '',
                publish_date TEXT DEFAULT '',
                raw_json TEXT DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS crawler_ts_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL,
                keyword TEXT NOT NULL,
                price REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'CNY',
                recorded_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS crawler_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL,
                url TEXT NOT NULL,
                status_code INTEGER NOT NULL DEFAULT 0,
                success INTEGER NOT NULL DEFAULT 0,
                error TEXT DEFAULT '',
                duration_ms REAL DEFAULT 0.0,
                crawled_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        self._conn.commit()

    def save_metadata(self, source_type: str, keyword: str, url: str, data: dict[str, Any]) -> int:
        """Save crawled metadata record. Returns row id."""
        cur = self._conn.execute(
            "INSERT INTO crawler_metadata (source_type, keyword, url, title, summary, author, publish_date, raw_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                source_type,
                keyword,
                url,
                data.get("title", ""),
                data.get("summary", ""),
                data.get("author", ""),
                data.get("publish_date", ""),
                json.dumps(data, ensure_ascii=False),
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def save_price(self, source_type: str, keyword: str, price: float, currency: str = "CNY") -> int:
        """Save a price time-series data point."""
        cur = self._conn.execute(
            "INSERT INTO crawler_ts_prices (source_type, keyword, price, currency) VALUES (?, ?, ?, ?)",
            (source_type, keyword, price, currency),
        )
        self._conn.commit()
        return cur.lastrowid

    def save_log(self, source_type: str, url: str, status_code: int, success: bool, error: str = "", duration_ms: float = 0.0) -> int:
        """Save a crawl log entry."""
        cur = self._conn.execute(
            "INSERT INTO crawler_log (source_type, url, status_code, success, error, duration_ms) VALUES (?, ?, ?, ?, ?, ?)",
            (source_type, url, status_code, 1 if success else 0, error, duration_ms),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_metadata(self, source_type: str, keyword: str, limit: int = 50) -> list[dict[str, Any]]:
        """Query metadata records."""
        rows = self._conn.execute(
            "SELECT * FROM crawler_metadata WHERE source_type = ? AND keyword = ? ORDER BY created_at DESC LIMIT ?",
            (source_type, keyword, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_price_history(self, source_type: str, keyword: str, limit: int = 100) -> list[dict[str, Any]]:
        """Query price time-series data."""
        rows = self._conn.execute(
            "SELECT * FROM crawler_ts_prices WHERE source_type = ? AND keyword = ? ORDER BY recorded_at DESC LIMIT ?",
            (source_type, keyword, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_logs(self, source_type: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]:
        """Query crawl logs, optionally filtered by source."""
        if source_type:
            rows = self._conn.execute(
                "SELECT * FROM crawler_log WHERE source_type = ? ORDER BY crawled_at DESC LIMIT ?",
                (source_type, limit),
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM crawler_log ORDER BY crawled_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def delete_record(self, record_id: int) -> bool:
        """Delete a metadata record by id."""
        cur = self._conn.execute("DELETE FROM crawler_metadata WHERE id = ?", (record_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def close(self) -> None:
        self._conn.close()
