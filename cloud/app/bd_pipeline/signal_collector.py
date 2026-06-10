"""Signal collector — listen to EventBus events, push new leads to BD pipeline."""

from __future__ import annotations

from typing import Any, Callable


class SignalCollector:
    """Collects signals from EventBus (competitor crawler, global intel) and routes to BD pipeline.

    Listens for published events and invokes registered handlers when
    relevant signal types are detected.
    """

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}

    def register(self, event_type: str, handler: Callable) -> None:
        """Register a handler for a specific event type."""
        self._handlers.setdefault(event_type, []).append(handler)

    def unregister(self, event_type: str, handler: Callable) -> bool:
        """Remove a handler registration."""
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)
            return True
        return False

    async def on_event(self, event_type: str, payload: dict[str, Any]) -> list[Any]:
        """Process an incoming event and invoke registered handlers."""
        results = []
        for handler in self._handlers.get(event_type, []):
            try:
                if hasattr(handler, "__call__"):
                    result = handler(payload)
                    if hasattr(result, "__await__"):
                        result = await result
                    results.append(result)
            except Exception:
                results.append(None)
        return results

    def collect_and_push(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Synchronously process a signal and return lead data."""
        return {
            "event_type": event_type,
            "collected": True,
            "lead_data": payload,
            "recommended_action": "push_to_pipeline",
        }
