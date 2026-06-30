"""世界模型 — 后台认知循环，读namespace找跨域模式关联。"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from cloud.app.agent_runtime.core.shared_state import SharedStateEntry, get_shared_state

logger = logging.getLogger(__name__)


@dataclass
class CognitionEntry:
    """认知声明——世界模型发现的跨域模式关联。"""

    cognition_id: str
    pattern: str
    description: str
    confidence: float  # 0-1
    evidence: list[str]  # 来源namespace路径
    agent_keys: list[str]  # 涉及Agent
    detected_at: str
    expires_at: str

    def to_dict(self) -> dict:
        return {
            "cognition_id": self.cognition_id,
            "pattern": self.pattern,
            "description": self.description,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "agent_keys": self.agent_keys,
            "detected_at": self.detected_at,
            "expires_at": self.expires_at,
        }


class WorldModelService:
    """跨域模式发现引擎，定时读取各Agent namespace输出寻找跨域关联。"""

    def __init__(self):
        self._cognitions: dict[str, CognitionEntry] = {}
        self._last_full_scan: Optional[str] = None

    def full_scan(self) -> list[CognitionEntry]:
        from cloud.app.agent_runtime.memory.world_model import get_world_model

        get_world_model()._full_scan()
        now = datetime.now(timezone.utc).isoformat()
        self._last_full_scan = now
        cognitions = self.get_cognitions(min_confidence=0.0)
        logger.info("世界模型全量扫描完成: %d 条认知发现", len(cognitions))
        return cognitions

    def incremental_scan(self, changed_namespaces: list[str]) -> list[CognitionEntry]:
        if not changed_namespaces:
            return []
        from cloud.app.agent_runtime.memory.world_model import get_world_model

        get_world_model()._incremental_scan(changed_namespaces)
        return self.get_cognitions(min_confidence=0.0)

    def get_cognitions(
        self,
        min_confidence: float = 0.0,
        agent_key: Optional[str] = None,
        limit: int = 20,
    ) -> list[CognitionEntry]:
        ss = get_shared_state()
        entries = ss.read("shared.cognition", min_confidence=min_confidence)
        results = []
        for e in entries:
            val = e.value if isinstance(e.value, dict) else {}
            agent_keys = val.get("agent_keys", [])
            if agent_key and agent_key not in agent_keys:
                continue
            results.append(
                CognitionEntry(
                    cognition_id=e.key,
                    pattern=val.get("pattern", ""),
                    description=val.get("description", ""),
                    confidence=e.confidence,
                    evidence=e.evidence,
                    agent_keys=agent_keys,
                    detected_at=e.timestamp or "",
                    expires_at="",
                )
            )
        results.sort(key=lambda x: (x.confidence, x.detected_at), reverse=True)
        return results[:limit]


class WorldModelLoop:
    """世界模型后台认知循环 — asyncio 定时扫描（每6h）+ SharedState 变更事件增量检查。"""

    AGENT_NAMESPACES = [
        "compliance.result",
        "analysis.result",
        "opportunity.result",
        "competitor.result",
        "suggestion.result",
    ]
    SCAN_INTERVAL = 6 * 3600
    RECENT_WINDOW = 24 * 3600
    COGNITION_NAMESPACE = "shared.cognition"
    POLL_INTERVAL = 60

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_full_scan: float = 0.0
        self._changed_ns: set[str] = set()

    async def start(self) -> None:
        """启动后台 asyncio 任务。"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())
        ss = get_shared_state()
        ss.subscribe(self._on_change)
        logger.info("WorldModelLoop started")

    async def stop(self) -> None:
        """停止后台循环。"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("WorldModelLoop stopped")

    def _on_change(self, entry: SharedStateEntry) -> None:
        """订阅 SharedState 变更，记录相关 namespace。"""
        ns = entry.namespace
        for prefix in ["compliance", "analysis", "opportunity", "competitor", "suggestion"]:
            if ns.startswith(prefix):
                self._changed_ns.add(ns)
                break

    async def _run(self) -> None:
        """主循环：每 6h 全量扫描 + 事件增量扫描。"""
        while self._running:
            try:
                now = time.time()
                if now - self._last_full_scan >= self.SCAN_INTERVAL:
                    await self._full_scan()
                    self._last_full_scan = now
                elif self._changed_ns:
                    namespaces = list(self._changed_ns)
                    self._changed_ns.clear()
                    await self._incremental_scan(namespaces)
            except Exception:
                logger.exception("WorldModelLoop cycle error")
            await asyncio.sleep(self.POLL_INTERVAL)

    async def _full_scan(self) -> None:
        """全量遍历所有 Agent namespace，读取最近 24h 事件，调用 LLM 发现跨域模式。"""
        logger.info("WorldModelLoop full scan")
        ss = get_shared_state()
        snapshot = {}
        for ns in self.AGENT_NAMESPACES:
            entries = ss.read(ns, min_confidence=0.3)
            if entries:
                recent = [e for e in entries if self._within_window(e)]
                if recent:
                    snapshot[ns] = {e.key: e.value for e in recent[-10:]}
        if not snapshot:
            return
        cognitions = await self._llm_reason(snapshot)
        for c in cognitions:
            self._write_cognition(ss, c)
        logger.info("WorldModelLoop full scan done: %d cognitions", len(cognitions))

    async def _incremental_scan(self, namespaces: list[str]) -> None:
        """增量扫描特定 namespace。"""
        ss = get_shared_state()
        snapshot = {}
        for ns in namespaces:
            if not any(ns.startswith(p) for p in ["compliance", "analysis", "opportunity", "competitor", "suggestion"]):
                continue
            entries = ss.read(ns, min_confidence=0.3)
            if entries:
                recent = [e for e in entries if self._within_window(e)]
                if recent:
                    snapshot[ns] = {e.key: e.value for e in recent[-5:]}
        if not snapshot:
            return
        cognitions = await self._llm_reason(snapshot, incremental=True)
        for c in cognitions:
            self._write_cognition(ss, c)
        logger.info("WorldModelLoop incremental scan done: %d cognitions", len(cognitions))

    @staticmethod
    def _within_window(entry: SharedStateEntry) -> bool:
        if not entry.timestamp:
            return True
        try:
            ts = datetime.fromisoformat(entry.timestamp)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - ts).total_seconds() < WorldModelLoop.RECENT_WINDOW
        except (ValueError, TypeError):
            return True

    async def _llm_reason(self, snapshot: dict, incremental: bool = False) -> list[dict]:
        """调用 LLM 跨域模式发现。"""
        if not snapshot:
            return []
        prompt = self._build_prompt(snapshot, incremental)
        try:
            from cloud.app.agent_runtime.runtime_llm import RuntimeLLM

            llm = RuntimeLLM()
            msg = [{"role": "user", "content": prompt}]
            result = await llm._call_ai_async(msg, temperature=0.3, force_level=2)
            reply = result.get("reply", "")
            return self._parse_output(reply)
        except Exception:
            logger.exception("WorldModelLoop LLM call failed")
            return []

    @staticmethod
    def _build_prompt(snapshot: dict, incremental: bool) -> str:
        lines = []
        for ns, data in snapshot.items():
            keys = list(data.keys())[:5]
            vals = [str(data[k])[:200] for k in keys]
            lines.append(f"<{ns}>")
            for v in vals:
                lines.append(f"  {v}")
        mode = "增量扫描" if incremental else "全量扫描"
        return (
            f"你是一个世界模型认知引擎，分析多 Agent namespace 数据发现跨域模式。\n"
            f"模式：{mode}\n\n"
            f"输入数据：\n" + "\n".join(lines) + "\n\n"
            "分析上述数据，找出跨域关联、异常模式或重要趋势。\n"
            "回复 JSON 数组，每个元素包含：\n"
            "  - pattern_description: 模式描述\n"
            "  - supporting_evidence: 证据列表\n"
            "  - confidence: 置信度 0-1\n"
            "  - recommended_action: 推荐行动\n"
            "Reply ONLY a valid JSON array."
        )

    @staticmethod
    def _parse_output(reply: str) -> list[dict]:
        reply = reply.strip()
        if reply.startswith("```"):
            reply = reply.split("\n", 1)[-1]
            reply = reply.rsplit("```", 1)[0]
        try:
            items = json.loads(reply)
            if not isinstance(items, list):
                items = [items]
        except (json.JSONDecodeError, TypeError):
            logger.warning("WorldModelLoop LLM output parse failed: %s", reply[:100])
            return []
        return [
            {
                "pattern_description": item.get("pattern_description", ""),
                "supporting_evidence": item.get("supporting_evidence", []),
                "confidence": float(item.get("confidence", 0.5)),
                "recommended_action": item.get("recommended_action", ""),
            }
            for item in items
            if isinstance(item, dict)
        ]

    @staticmethod
    def _write_cognition(ss, cognition: dict) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        entry = SharedStateEntry(
            namespace=WorldModelLoop.COGNITION_NAMESPACE,
            key=f"cognition.{ts}",
            value={
                "pattern_description": cognition.get("pattern_description", ""),
                "supporting_evidence": cognition.get("supporting_evidence", []),
                "confidence": cognition.get("confidence", 0.5),
                "recommended_action": cognition.get("recommended_action", ""),
            },
            agent_key="world_model",
            confidence=cognition.get("confidence", 0.5),
            evidence=cognition.get("supporting_evidence", []),
        )
        ss.write(entry, caller_agent_key="world_model")
        logger.info(
            "Cognition written: pattern=%s confidence=%.2f",
            cognition.get("pattern_description", "")[:50],
            cognition.get("confidence", 0.5),
        )


_global_wm_loop: Optional[WorldModelLoop] = None


def get_world_model_loop() -> WorldModelLoop:
    global _global_wm_loop
    if _global_wm_loop is None:
        _global_wm_loop = WorldModelLoop()
    return _global_wm_loop
