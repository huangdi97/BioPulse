"""本地缓存数据库。缓存 Cloud API 响应，TTL 600 秒。"""

import sqlite3
import os
import time
import json

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "patient_engage_cache.db",
)

CACHE_TTL = 600


def init_cache_db():
    """初始化缓存数据库，创建 api_cache 表。"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS api_cache (
            cache_key TEXT PRIMARY KEY,
            response TEXT,
            cached_at REAL,
            ttl INTEGER DEFAULT ?
        )
    """,
        (CACHE_TTL,),
    )
    conn.commit()
    conn.close()


def get_cache(key: str) -> dict | None:
    """获取缓存，如果未过期则返回数据，否则返回 None。"""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT response, cached_at, ttl FROM api_cache WHERE cache_key=?",
        (key,),
    ).fetchone()
    conn.close()
    if row:
        if time.time() - row[1] < row[2]:
            return json.loads(row[0])
    return None


def set_cache(key: str, data: dict, ttl: int = CACHE_TTL):
    """写入缓存，key 相同则覆盖。"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO api_cache (cache_key, response, cached_at, ttl) VALUES (?, ?, ?, ?)",
        (key, json.dumps(data), time.time(), ttl),
    )
    conn.commit()
    conn.close()
