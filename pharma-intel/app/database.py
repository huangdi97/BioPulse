"""本地缓存数据库。缓存 Cloud API 响应，TTL 30 分钟。"""

import sqlite3
import os
import time
import json

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "pharma_intel_cache.db",
)


def init_cache_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_cache (
            cache_key TEXT PRIMARY KEY,
            response TEXT,
            cached_at REAL,
            ttl INTEGER DEFAULT 1800
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kol_profiles (
            researcher_id TEXT PRIMARY KEY,
            profile_data TEXT,
            last_updated TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_cache(key: str) -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT response, cached_at, ttl FROM api_cache WHERE cache_key=?", (key,)
    ).fetchone()
    conn.close()
    if row:
        if time.time() - row[1] < row[2]:
            return json.loads(row[0])
    return None


def set_cache(key: str, data: dict, ttl: int = 1800):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO api_cache (cache_key, response, cached_at, ttl) VALUES (?, ?, ?, ?)",
        (key, json.dumps(data), time.time(), ttl),
    )
    conn.commit()
    conn.close()
