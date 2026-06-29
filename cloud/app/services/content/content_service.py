from datetime import datetime, timedelta
from typing import Optional


class ContentService:
    def __init__(self):
        self._contents: dict[str, dict] = {}
        self._view_logs: list[dict] = []
        self._next_id = 1

    def _next_content_id(self) -> str:
        cid = f"CONT-{self._next_id:04d}"
        self._next_id += 1
        return cid

    def upload_content(
        self,
        title: str,
        content_type: str,
        tags: list[str],
        hcp_target: bool = False,
        expire_days: Optional[int] = None,
    ) -> dict:
        cid = self._next_content_id()
        now = datetime.utcnow()
        expires_at = (now + timedelta(days=expire_days)).isoformat() if expire_days else None
        entry = {
            "id": cid,
            "title": title,
            "type": content_type,
            "tags": tags,
            "hcp_target": hcp_target,
            "status": "pending",
            "created_at": now.isoformat(),
            "expires_at": expires_at,
            "approved_at": None,
            "rejected_at": None,
            "rejection_reason": None,
        }
        self._contents[cid] = entry
        return dict(entry)

    def approve_content(self, content_id: str) -> Optional[dict]:
        entry = self._contents.get(content_id)
        if not entry or entry["status"] != "pending":
            return None
        entry["status"] = "approved"
        entry["approved_at"] = datetime.utcnow().isoformat()
        return dict(entry)

    def reject_content(self, content_id: str, reason: str = "") -> Optional[dict]:
        entry = self._contents.get(content_id)
        if not entry or entry["status"] != "pending":
            return None
        entry["status"] = "rejected"
        entry["rejected_at"] = datetime.utcnow().isoformat()
        entry["rejection_reason"] = reason
        return dict(entry)

    def record_clm_view(
        self,
        representative: str,
        hcp_id: str,
        feedback: Optional[str] = None,
    ) -> dict:
        now = datetime.utcnow().isoformat()
        log = {
            "representative": representative,
            "hcp_id": hcp_id,
            "feedback": feedback,
            "viewed_at": now,
        }
        self._view_logs.append(log)
        return dict(log)

    def list_approved(self) -> list[dict]:
        approved = [e for e in self._contents.values() if e["status"] == "approved"]
        now = datetime.utcnow()
        result = []
        for e in approved:
            if e["expires_at"] and datetime.fromisoformat(e["expires_at"]) < now:
                continue
            result.append(dict(e))
        return result
