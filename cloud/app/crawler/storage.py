"""SQLite storage for competitor intelligence crawler records."""

from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime
from typing import Any, Type

from pydantic import BaseModel

from cloud.app.crawler.models import BiddingRecord, CompetitorProduct, PriceRecord, PublicOpinion

CRAWLER_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "data",
    "crawler.db",
)


MODEL_TABLES: dict[type[BaseModel], str] = {
    CompetitorProduct: "competitor_products",
    PriceRecord: "price_records",
    PublicOpinion: "public_opinions",
    BiddingRecord: "bidding_records",
}


class CrawlerStorage:
    """Persist crawler output in SQLite relational and time-series tables."""

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize storage, creating the database and schema if needed."""
        self.db_path = db_path or CRAWLER_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Return a new SQLite connection with row_factory set to sqlite3.Row."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Create tables and indexes if they do not exist."""
        with self.get_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS competitor_products ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "name TEXT NOT NULL, "
                "company TEXT NOT NULL DEFAULT '', "
                "category TEXT NOT NULL DEFAULT '', "
                "target TEXT NOT NULL DEFAULT '', "
                "mechanism TEXT NOT NULL DEFAULT '', "
                "phase TEXT NOT NULL DEFAULT '', "
                "price REAL, "
                "market_share REAL, "
                "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, "
                "updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP"
                ")"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_competitor_products_name ON competitor_products(name)")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS price_records ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "product_id INTEGER NOT NULL, "
                "price REAL NOT NULL, "
                "province TEXT NOT NULL DEFAULT '', "
                "date TEXT NOT NULL, "
                "source TEXT NOT NULL DEFAULT '', "
                "timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP"
                ")"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_price_records_timestamp ON price_records(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_price_records_product_date ON price_records(product_id, date)")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS public_opinions ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "product_id INTEGER NOT NULL, "
                "platform TEXT NOT NULL, "
                "title TEXT NOT NULL DEFAULT '', "
                "content TEXT NOT NULL DEFAULT '', "
                "sentiment TEXT NOT NULL DEFAULT 'neutral', "
                "publish_date TEXT, "
                "url TEXT NOT NULL DEFAULT '', "
                "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP"
                ")"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_public_opinions_product ON public_opinions(product_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_public_opinions_platform ON public_opinions(platform)")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS bidding_records ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "product_id INTEGER NOT NULL, "
                "province TEXT NOT NULL DEFAULT '', "
                "winning_price REAL, "
                "manufacturer TEXT NOT NULL DEFAULT '', "
                "round TEXT NOT NULL DEFAULT '', "
                "date TEXT NOT NULL, "
                "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP"
                ")"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_bidding_records_product_date ON bidding_records(product_id, date)")
            conn.commit()

    def save_record(self, record: BaseModel) -> int:
        """Persist a crawler model instance and return the newly assigned row id.

        Args:
            record: A Pydantic model instance (CompetitorProduct, PriceRecord, etc.).

        Returns:
            The auto-incremented row id.

        Raises:
            ValueError: If the model type is not registered in MODEL_TABLES.
        """
        model_type = self._model_type(record)
        table = MODEL_TABLES[model_type]
        payload = self._serialize(record)
        payload.pop("id", None)
        columns = list(payload.keys())
        placeholders = ", ".join("?" for _ in columns)
        column_sql = ", ".join(f'"{col}"' for col in columns)
        values = [payload[column] for column in columns]
        with self.get_connection() as conn:
            cursor = conn.execute(f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})", values)
            conn.commit()
            return int(cursor.lastrowid)

    def query_records(
        self,
        model: Type[BaseModel],
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Query records by model type with optional equality/IN filters.

        Args:
            model: A registered Pydantic model class.
            filters: Column-to-value(s) mapping for WHERE clause filtering.

        Returns:
            A list of dicts, each representing a row.

        Raises:
            ValueError: If the model is not registered in MODEL_TABLES.
        """
        if model not in MODEL_TABLES:
            raise ValueError(f"Unsupported crawler model: {model}")
        table = MODEL_TABLES[model]
        filters = filters or {}
        clauses = []
        params = []
        for key, value in filters.items():
            if isinstance(value, (list, tuple, set)):
                placeholders = ", ".join("?" for _ in value)
                clauses.append(f"{key} IN ({placeholders})")
                params.extend(value)
            else:
                clauses.append(f"{key} = ?")
                params.append(value)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        order_by = " ORDER BY timestamp DESC" if model is PriceRecord else " ORDER BY id DESC"
        with self.get_connection() as conn:
            rows = conn.execute(f"SELECT * FROM {table}{where}{order_by}", params).fetchall()
            return [dict(row) for row in rows]

    # -- internal helpers ------------------------------------------------------

    def _model_type(self, record: BaseModel) -> type[BaseModel]:
        # Walk MODEL_TABLES to find which registered model the record is an instance of.
        if isinstance(record, BaseModel):
            for model in MODEL_TABLES:
                if isinstance(record, model):
                    return model
        raise ValueError(f"Unsupported crawler record type: {type(record)}")

    def _serialize(self, record: BaseModel) -> dict[str, Any]:
        # Convert a Pydantic model to a dict, normalizing date/datetime to ISO strings.
        payload = record.model_dump()
        for key, value in list(payload.items()):
            if isinstance(value, (date, datetime)):
                payload[key] = value.isoformat()
        return payload


_default_storage: CrawlerStorage | None = None


def get_storage() -> CrawlerStorage:
    """Return the process-wide singleton CrawlerStorage, lazily created."""
    global _default_storage
    if _default_storage is None:
        _default_storage = CrawlerStorage()
    return _default_storage


def save_record(record: BaseModel) -> int:
    """Convenience function: persist a record via the default storage singleton."""
    return get_storage().save_record(record)


def query_records(model: Type[BaseModel], filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Convenience function: query records via the default storage singleton."""
    return get_storage().query_records(model, filters)


__all__ = ["CRAWLER_DB_PATH", "CrawlerStorage", "query_records", "save_record"]
