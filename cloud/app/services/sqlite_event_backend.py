"""SQLite backend for event bus delivery."""

from cloud.app.repositories import EventDeliveryLogRepository


class SqliteEventBackend:
    """SQLite 事件后端（默认实现）。"""

    def deliver(
        self,
        db,
        delivery_repo: EventDeliveryLogRepository,
        message_id: str,
        targets: list,
        event_type: str,
        source_end: str,
        payload_json: str,
    ) -> list:
        results = []
        for i, target in enumerate(targets):
            is_delivered = i == 0
            status_val = "delivered" if is_delivered else "pending"
            resp = "OK: 200 (simulated)" if is_delivered else ""
            err = "" if is_delivered else f"simulated pending for {target}"
            dur = 25 if is_delivered else 0
            delivery_repo.create(
                {
                    "message_id": message_id,
                    "target_end": target,
                    "delivery_status": status_val,
                    "attempt": 1,
                    "response_summary": resp,
                    "duration_ms": dur,
                    "error_message": err,
                }
            )
            results.append(
                {
                    "target_end": target,
                    "delivery_status": status_val,
                    "error_message": err,
                }
            )
        return results

    def subscribe(self, target_end: str, event_types: list, callback_url: str = "") -> dict:
        return {
            "acknowledged": True,
            "target_end": target_end,
            "event_types": event_types,
            "callback_url": callback_url,
        }
