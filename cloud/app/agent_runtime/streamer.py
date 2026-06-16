"""Agent 执行过程流式输出。将执行状态实时推送给前端。"""

import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator

logger = logging.getLogger(__name__)


class AgentStreamer:
    """Agent 执行过程流式输出。将执行状态实时推送给前端。"""

    STREAM_EVENTS = [
        "agent.start",
        "agent.tool_call",
        "agent.tool_result",
        "agent.llm_call",
        "agent.llm_result",
        "agent.thinking",
        "agent.error",
        "agent.end",
    ]

    def __init__(self):
        self._streams: dict[str, list[dict]] = {}
        self._subscribers: dict[str, list[asyncio.Event]] = {}

    def stream(self, trace_id: str, event_type: str, data: dict):
        """stream."""
        if event_type not in self.STREAM_EVENTS:
            logger.warning("Unknown stream event type: %s", event_type)
            return
        entry = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
        if trace_id not in self._streams:
            self._streams[trace_id] = []
        self._streams[trace_id].append(entry)
        if trace_id in self._subscribers:
            for event in self._subscribers[trace_id]:
                event.set()

    def get_stream(self, trace_id: str) -> AsyncGenerator[str, None]:
        """get stream."""
        if trace_id not in self._subscribers:
            self._subscribers[trace_id] = []

        async def _generate():
            seen = 0
            while True:
                events = self._streams.get(trace_id, [])
                while seen < len(events):
                    entry = events[seen]
                    seen += 1
                    yield f"event: {entry['event']}\ndata: {json.dumps(entry['data'], ensure_ascii=False)}\n\n"
                if events and events[-1]["event"] == "agent.end":
                    break
                event = asyncio.Event()
                self._subscribers[trace_id].append(event)
                try:
                    await asyncio.wait_for(event.wait(), timeout=30)
                except asyncio.TimeoutError:
                    break
                finally:
                    if event in self._subscribers[trace_id]:
                        self._subscribers[trace_id].remove(event)
            yield "event: done\ndata: {}\n\n"

        return _generate()

    def has_stream(self, trace_id: str) -> bool:
        """has stream."""
        return trace_id in self._subscribers and len(self._subscribers[trace_id]) > 0
