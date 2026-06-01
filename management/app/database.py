import json
import os
import sqlite3
import time

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "management_cache.db",
)


def init_cache_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_cache (
            cache_key TEXT PRIMARY KEY,
            response TEXT,
            cached_at REAL,
            ttl INTEGER DEFAULT 60
        )
    """)
    conn.commit()
    conn.close()


def get_cache(key: str) -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT response, cached_at, ttl FROM api_cache WHERE cache_key=?", (key,)).fetchone()
    conn.close()
    if row and time.time() - row[1] < row[2]:
        return json.loads(row[0])
    return None


def set_cache(key: str, data: dict, ttl: int = 60):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO api_cache (cache_key, response, cached_at, ttl) VALUES (?, ?, ?, ?)",
        (key, json.dumps(data), time.time(), ttl),
    )
    conn.commit()
    conn.close()
