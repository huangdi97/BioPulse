"""本地缓存数据库。缓存 Cloud API 响应，TTL 30 分钟。"""

import json
import os
import sqlite3
import time

from shared.database import SQLiteCache

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "pharma_intel_cache.db",
)

_cache = SQLiteCache(DB_PATH, default_ttl=1800)


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
    return _cache.get_cache(key)


def set_cache(key: str, data: dict, ttl: int = 1800):
    _cache.set_cache(key, data, ttl)
