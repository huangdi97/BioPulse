"""EventBridge — push new crawl results to EventBus to trigger downstream analysis."""

from __future__ import annotations

import uuid
from typing import Any

from cloud.app.competitor_crawler.engine import CrawlResult


class EventBridge:
    """Pushes crawl results to the EventBus for downstream consumers."""

    def __init__(self, event_bus_service: Any = None):
        self._event_bus = event_bus_service

    def set_event_bus(self, event_bus_service: Any) -> None:
        """Set or replace the EventBus service instance."""
        self._event_bus = event_bus_service

    async def publish(self, result: CrawlResult) -> dict[str, Any]:
        """Publish a crawl result to the EventBus."""
        if not self._event_bus:
            return {"published": False, "error": "EventBus not configured"}

        payload = {
            "source": result.source,
            "url": result.url,
            "success": result.success,
            "status_code": result.status_code,
            "content_length": len(result.content),
            "metadata": result.metadata,
            "timestamp": result.timestamp.isoformat() if hasattr(result.timestamp, "isoformat") else str(result.timestamp),
        }

        try:
            return self._event_bus.publish_message(
                event_type="competitor.crawl.completed",
                source_entity_type="crawler",
                source_entity_id=f"crawl:{result.source}:{uuid.uuid4()}",
                payload=payload,
                correlation_id=f"corr:{uuid.uuid4()}",
            )
        except Exception as exc:
            return {"published": False, "error": str(exc)}

    async def publish_batch(self, results: list[CrawlResult]) -> list[dict[str, Any]]:
        """Publish multiple crawl results."""
        outcomes = []
        for result in results:
            outcome = await self.publish(result)
            outcomes.append(outcome)
        return outcomes
