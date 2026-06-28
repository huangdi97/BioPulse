"""多源数据接入 — 支持 REST API / WebSocket / 文件导入 / DB 轮询等来源。"""

import json
import logging
import threading
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

DEFAULT_INGESTION_PATH = "data/ingestion_log.json"

RecordHandler = Callable[[dict], None]


class BaseSource(ABC):
    """数据源抽象基类。"""

    @abstractmethod
    def read(self) -> list[dict]:
        """读取一批原始记录。"""

    @abstractmethod
    def source_name(self) -> str:
        """返回数据源名称。"""


class DataIngestion:
    """多源数据接入 — 统一接收不同来源的数据并转成内部标准格式。

    支持的数据源类型：
    - REST API 推送（ingest_record 直接接收）
    - 文件导入（支持 JSON / CSV / Parquet）
    - DB 轮询（通过回调 Source 类）
    - WebSocket 流（ingest_record 实时接收）
    """

    def __init__(self, storage_path: str = DEFAULT_INGESTION_PATH):
        self._path = Path(storage_path)
        self._lock = threading.Lock()
        self._sources: dict[str, BaseSource] = {}
        self._handlers: list[RecordHandler] = []
        self._ingested_count: dict[str, int] = defaultdict(int)
        self._log: list[dict] = []
        self._load()

    def _load(self):
        if self._path.exists():
            try:
                with open(self._path) as f:
                    data = json.load(f)
                self._ingested_count = defaultdict(int, data.get("counts", {}))
                self._log = data.get("log", [])
                if len(self._log) > 1000:
                    self._log = self._log[-1000:]
            except Exception as e:
                logger.warning("DataIngestion: failed to load %s: %s", self._path, e)

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(
                {
                    "counts": dict(self._ingested_count),
                    "log": self._log[-500:],
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        tmp.replace(self._path)

    def register_source(self, source: BaseSource):
        """注册一个数据源（用于轮询拉取）。

        Args:
            source: 实现了 BaseSource 的实例
        """
        with self._lock:
            self._sources[source.source_name()] = source

    def register_handler(self, handler: RecordHandler):
        """注册记录处理回调（如发给 DataAlignment）。

        Args:
            handler: 接收 dict 记录的回调函数
        """
        with self._lock:
            self._handlers.append(handler)

    def ingest_record(self, source: str, record: dict) -> dict:
        """接收单条记录（REST / WebSocket 推送）。

        Args:
            source: 来源标识
            record: 原始记录 dict（需含至少一个标识字段）

        Returns:
            标准化后的记录
        """
        normalized = self._normalize(source, record)
        with self._lock:
            self._ingested_count[source] += 1
            self._log.append(
                {
                    "source": source,
                    "record_id": normalized.get("id", ""),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            handlers = list(self._handlers)
            self._save()
        for handler in handlers:
            try:
                handler(normalized)
            except Exception as e:
                logger.error("DataIngestion: handler failed for %s: %s", source, e)
        return normalized

    def ingest_batch(self, source: str, records: list[dict]) -> list[dict]:
        """批量接入多条记录。

        Args:
            source: 来源标识
            records: 原始记录列表

        Returns:
            标准化后的记录列表
        """
        return [self.ingest_record(source, r) for r in records]

    def poll_sources(self):
        """轮询所有已注册的数据源。"""
        with self._lock:
            sources = dict(self._sources)
        for name, source in sources.items():
            try:
                records = source.read()
                if records:
                    self.ingest_batch(name, records)
                    logger.info("DataIngestion: polled %s, got %d records", name, len(records))
            except Exception as e:
                logger.error("DataIngestion: poll %s failed: %s", name, e)

    def _normalize(self, source: str, record: dict) -> dict:
        return {
            "id": record.get("id") or record.get("record_id") or "",
            "source": source,
            "type": record.get("type", "unknown"),
            "data": record.get("data", record),
            "raw": record,
            "ingested_at": datetime.utcnow().isoformat(),
        }

    def get_stats(self) -> dict[str, Any]:
        """返回接入统计。"""
        with self._lock:
            return {
                "total_by_source": dict(self._ingested_count),
                "total_records": sum(self._ingested_count.values()),
                "source_count": len(self._sources),
                "handler_count": len(self._handlers),
                "recent_log_count": len(self._log),
            }
