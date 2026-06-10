"""本地缓存数据库。缓存 Cloud API 响应，TTL 300 秒。"""

from shared.database import make_cache_db

_cache = make_cache_db("market_access", ttl=300)
init_cache_db = _cache.init_cache_db
get_cache = _cache.get_cache
set_cache = _cache.set_cache
