"""SSE 流式路由，基于 Redis Streams 推送实时事件。"""

import asyncio
import json
import uuid
from typing import Optional

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse

from cloud.app.services.event_bus_service import RedisEventBus

router = APIRouter(prefix="/events/stream", tags=["Event Stream"])


def _sse_event(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/{stream}")
async def stream_events(
    request: Request,
    stream: str,
    group: str = Query("default"),
    consumer: Optional[str] = Query(None),
):
    if consumer is None:
        consumer = f"consumer-{uuid.uuid4().hex[:8]}"

    bus = RedisEventBus()

    async def event_generator():
        heartbeat_interval = 30
        last_heartbeat = 0

        while True:
            if await request.is_disconnected():
                break

            now = asyncio.get_event_loop().time()
            if now - last_heartbeat >= heartbeat_interval:
                yield ": heartbeat\n\n"
                last_heartbeat = now

            if bus.is_available():
                messages = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: bus.subscribe(stream, group, consumer, timeout_ms=5000),
                )
                if messages:
                    for msg in messages:
                        yield _sse_event(msg)
                        msg_id = msg.get("id")
                        if msg_id:
                            await asyncio.get_event_loop().run_in_executor(
                                None,
                                lambda mid=msg_id: bus.ack(stream, group, mid),
                            )
                    continue

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
