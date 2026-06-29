from datetime import datetime
from uuid import uuid4


class EventService:
    def __init__(self):
        self._events: dict[str, dict] = {}

    def create_event(
        self,
        name: str,
        type: str,
        date: str,
        agenda: str,
        hcp_ids: list[str],
    ) -> dict:
        event_id = uuid4().hex[:12]
        now = datetime.utcnow().isoformat()
        event = {
            "id": event_id,
            "name": name,
            "type": type,
            "date": date,
            "agenda": agenda,
            "hcp_ids": list(hcp_ids),
            "checked_in_hcp_ids": [],
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }
        self._events[event_id] = event
        return dict(event)

    def invite_hcps(self, event_id: str, hcp_ids: list[str]) -> dict:
        event = self._get_event(event_id)
        existing = set(event["hcp_ids"])
        for hid in hcp_ids:
            if hid not in existing:
                event["hcp_ids"].append(hid)
                existing.add(hid)
        event["updated_at"] = datetime.utcnow().isoformat()
        return dict(event)

    def check_in(self, event_id: str, hcp_id: str) -> dict:
        event = self._get_event(event_id)
        if hcp_id not in event["hcp_ids"]:
            raise ValueError(f"HCP {hcp_id} is not invited to event {event_id}")
        if hcp_id not in event["checked_in_hcp_ids"]:
            event["checked_in_hcp_ids"].append(hcp_id)
        event["updated_at"] = datetime.utcnow().isoformat()
        return dict(event)

    def approve_event(self, event_id: str) -> dict:
        event = self._get_event(event_id)
        if event["status"] != "pending":
            raise ValueError(f"Event {event_id} is not in pending status")
        event["status"] = "approved"
        event["updated_at"] = datetime.utcnow().isoformat()
        return dict(event)

    def reject_event(self, event_id: str) -> dict:
        event = self._get_event(event_id)
        if event["status"] != "pending":
            raise ValueError(f"Event {event_id} is not in pending status")
        event["status"] = "rejected"
        event["updated_at"] = datetime.utcnow().isoformat()
        return dict(event)

    def get_summary(self, event_id: str) -> dict:
        event = self._get_event(event_id)
        return {
            "id": event["id"],
            "name": event["name"],
            "type": event["type"],
            "date": event["date"],
            "status": event["status"],
            "total_invited": len(event["hcp_ids"]),
            "total_checked_in": len(event["checked_in_hcp_ids"]),
            "checked_in_hcp_ids": list(event["checked_in_hcp_ids"]),
        }

    def _get_event(self, event_id: str) -> dict:
        event = self._events.get(event_id)
        if event is None:
            raise KeyError(f"Event {event_id} not found")
        return event
