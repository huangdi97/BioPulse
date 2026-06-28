"""Schema 对齐 + 去重 + 补全 — 将多源异构数据转成统一格式。"""

import hashlib
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

DEFAULT_ALIGNMENT_PATH = "data/alignment_cache.json"

AlignHandler = Callable[[dict], dict]


class DataAlignment:
    """对 DataIngestion 接入的多源数据进行 schema 对齐、去重和字段补全。

    核心流程：
    1. schema 对齐：将不同来源的字段映射到标准 schema
    2. 去重：基于关键字段 hash 去除重复记录
    3. 补全：用默认值 / 派生值补全缺失字段
    """

    def __init__(self, schema: dict[str, type | tuple[type, Any]] | None = None, storage_path: str = DEFAULT_ALIGNMENT_PATH):
        self._path = Path(storage_path)
        self._lock = threading.Lock()
        self._seen_hashes: set[str] = set()
        self._duplicate_count = 0
        self._aligned_count = 0
        self._handlers: list[AlignHandler] = []

        self._schema: dict[str, type | tuple[type, Any]] = schema or {
            "id": str,
            "source": str,
            "type": str,
            "timestamp": str,
            "data": dict,
        }
        self._dedup_keys: list[str] = ["id", "source"]
        self._load()

    def _load(self):
        if self._path.exists():
            try:
                with open(self._path) as f:
                    data = json.load(f)
                self._seen_hashes = set(data.get("seen_hashes", []))
                self._duplicate_count = data.get("duplicate_count", 0)
                self._aligned_count = data.get("aligned_count", 0)
            except Exception as e:
                logger.warning("DataAlignment: failed to load %s: %s", self._path, e)

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(
                {
                    "seen_hashes": list(self._seen_hashes)[-10000:],
                    "duplicate_count": self._duplicate_count,
                    "aligned_count": self._aligned_count,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        tmp.replace(self._path)

    def register_handler(self, handler: AlignHandler):
        """注册对齐后处理回调。

        Args:
            handler: 接收对齐后的 dict，返回 dict（可进一步变换）
        """
        with self._lock:
            self._handlers.append(handler)

    def set_dedup_keys(self, keys: list[str]):
        """设置去重关键字段列表。

        Args:
            keys: 字段名列表，组合 hash 作为去重指纹
        """
        with self._lock:
            self._dedup_keys = keys

    def set_schema(self, schema: dict[str, type | tuple[type, Any]]):
        """设置目标 schema。

        Args:
            schema: 字段名到类型（或 (类型, 默认值)）的映射
        """
        with self._lock:
            self._schema = schema

    def align(self, record: dict) -> dict | None:
        """对齐单条记录 — schema 映射 + 去重 + 补全。

        Args:
            record: DataIngestion 输出的标准化记录

        Returns:
            对齐后的记录，若为重复则返回 None
        """
        aligned = self._map_schema(record)
        if self._is_duplicate(aligned):
            return None
        aligned = self._fill_missing(aligned)

        with self._lock:
            self._aligned_count += 1
            handlers = list(self._handlers)
        for handler in handlers:
            try:
                aligned = handler(aligned)
            except Exception as e:
                logger.error("DataAlignment: handler failed: %s", e)
        return aligned

    def align_batch(self, records: list[dict]) -> list[dict]:
        """批量对齐记录。

        Args:
            records: 标准化记录列表

        Returns:
            非重复的对齐后记录列表
        """
        return [a for r in records if (a := self.align(r)) is not None]

    def _map_schema(self, record: dict) -> dict:
        mapped: dict[str, Any] = {}
        schema_fields = list(self._schema.keys())
        for field in schema_fields:
            if field in record:
                mapped[field] = record[field]
            else:
                mapped[field] = None
        mapped["_source_raw"] = record.get("raw", record)
        mapped["_aligned_at"] = datetime.utcnow().isoformat()
        return mapped

    def _is_duplicate(self, record: dict) -> bool:
        fingerprint = self._compute_fingerprint(record)
        with self._lock:
            if fingerprint in self._seen_hashes:
                self._duplicate_count += 1
                return True
            self._seen_hashes.add(fingerprint)
            if len(self._seen_hashes) > 50000:
                self._seen_hashes = set(list(self._seen_hashes)[-25000:])
            return False

    def _compute_fingerprint(self, record: dict) -> str:
        parts = []
        for key in self._dedup_keys:
            val = record.get(key)
            parts.append(str(val) if val is not None else "")
        raw = "|".join(parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _fill_missing(self, record: dict) -> dict:
        for field, spec in self._schema.items():
            if record.get(field) is not None:
                continue
            if isinstance(spec, tuple):
                expected_type, default = spec
                record[field] = default
            else:
                try:
                    if spec is str:
                        record[field] = ""
                    elif spec is int:
                        record[field] = 0
                    elif spec is float:
                        record[field] = 0.0
                    elif spec is bool:
                        record[field] = False
                    elif spec is list:
                        record[field] = []
                    elif spec is dict:
                        record[field] = {}
                    else:
                        record[field] = None
                except Exception:
                    record[field] = None
        return record

    def get_stats(self) -> dict[str, Any]:
        """返回对齐统计。"""
        with self._lock:
            return {
                "aligned_count": self._aligned_count,
                "duplicate_count": self._duplicate_count,
                "seen_unique": len(self._seen_hashes),
                "schema_fields": list(self._schema.keys()),
                "dedup_keys": list(self._dedup_keys),
            }

    def reset_dedup_cache(self):
        """清空去重缓存。"""
        with self._lock:
            self._seen_hashes.clear()
            self._duplicate_count = 0
            self._save()
