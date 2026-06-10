"""本地缓存数据库。缓存 Cloud API 响应，TTL 600 秒。"""

from shared.database import make_cache_db

_cache = make_cache_db("clinical_ops", ttl=600)
init_cache_db = _cache.init_cache_db
get_cache = _cache.get_cache
set_cache = _cache.set_cache
