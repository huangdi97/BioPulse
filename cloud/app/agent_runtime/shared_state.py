"""SharedState 结构化数据模型 — 设计文档 §3.3"""

import logging
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Generator, List

logger = logging.getLogger(__name__)


@dataclass
class SharedStateEntry:
    namespace: str
    key: str
    value: Any
    confidence: float = 1.0
    agent_key: str = ""
    timestamp: str = ""
    version: int = 1
    evidence: List[str] = field(default_factory=list)


def _validate_namespace(caller_agent_key: str, namespace: str) -> None:
    from shared.agent_identity import get_identity

    identity = get_identity(caller_agent_key)
    allowed = identity.get("memory_namespace", caller_agent_key)
    if not namespace.startswith(allowed):
        raise PermissionError(f"Agent {caller_agent_key} (namespace={allowed}) 无权写入 namespace={namespace}")


class SharedState:
    def __init__(self):
        self._lock = threading.Lock()
        self._entries: List[SharedStateEntry] = []
        self._watchers: dict[str, List[callable]] = {}
        self._version_counter = 0

    def write(self, entry: SharedStateEntry, caller_agent_key: str | None = None) -> None:
        if caller_agent_key:
            _validate_namespace(caller_agent_key, entry.namespace)
        if entry.confidence < 0.3:
            logger.warning(
                "Low confidence write: namespace=%s key=%s confidence=%.2f",
                entry.namespace,
                entry.key,
                entry.confidence,
            )
        if not entry.evidence:
            logger.warning(
                "Empty evidence on write: namespace=%s key=%s",
                entry.namespace,
                entry.key,
            )
        with self._lock:
            self._version_counter += 1
            entry.version = self._version_counter
            entry.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            self._entries.append(entry)
            self._notify_watchers(entry)

    def read(
        self,
        namespace: str,
        key: str | None = None,
        min_confidence: float = 0.0,
    ) -> List[SharedStateEntry]:
        results = []
        with self._lock:
            for e in self._entries:
                if e.namespace != namespace:
                    continue
                if key is not None and not e.key.startswith(key):
                    continue
                if e.confidence < min_confidence:
                    continue
                results.append(e)
        return results

    def watch(self, namespace_pattern: str) -> Generator[SharedStateEntry, None, None]:
        import queue

        q: queue.Queue[SharedStateEntry | None] = queue.Queue()

        def _callback(entry: SharedStateEntry) -> None:
            if re.match(namespace_pattern, entry.namespace):
                q.put(entry)

        with self._lock:
            self._watchers.setdefault(namespace_pattern, []).append(_callback)

        try:
            while True:
                entry = q.get()
                if entry is None:
                    break
                yield entry
        finally:
            with self._lock:
                if namespace_pattern in self._watchers:
                    self._watchers[namespace_pattern] = [cb for cb in self._watchers[namespace_pattern] if cb is not _callback]

    def _notify_watchers(self, entry: SharedStateEntry) -> None:
        for pattern, callbacks in list(self._watchers.items()):
            if re.match(pattern, entry.namespace):
                for cb in callbacks:
                    try:
                        cb(entry)
                    except Exception:
                        logger.exception("Watcher callback failed for pattern=%s", pattern)
