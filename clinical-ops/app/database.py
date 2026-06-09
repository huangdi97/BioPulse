"""本地缓存数据库。缓存 Cloud API 响应，TTL 600 秒。"""

import os

from shared.database import SQLiteCache

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "clinical_ops_cache.db",
)

CACHE_TTL = 600

_cache = SQLiteCache(DB_PATH, default_ttl=CACHE_TTL)


def init_cache_db():
    """初始化缓存数据库，创建 api_cache 表。"""
    _cache.init_cache_db()


def get_cache(key: str) -> dict | None:
    """获取缓存，如果未过期则返回数据，否则返回 None。"""
    return _cache.get_cache(key)


def set_cache(key: str, data: dict, ttl: int = CACHE_TTL):
    """写入缓存，key 相同则覆盖。"""
    _cache.set_cache(key, data, ttl)
