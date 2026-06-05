import os
import sqlite3
from typing import List

_CLOUD_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "cloud.db",
)


def _get_cloud_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_CLOUD_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _read_kg_entities(entity_types: List[str]) -> List[dict]:
    conn = _get_cloud_conn()
    try:
        placeholders = ",".join("?" for _ in entity_types)
        rows = conn.execute(
            f"SELECT entity_id, entity_type, name, properties FROM kg_entities WHERE entity_type IN ({placeholders}) AND status = 'active'",
            entity_types,
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
