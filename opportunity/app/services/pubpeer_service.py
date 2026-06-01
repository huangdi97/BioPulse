import json
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Optional

from opportunity.app.repositories import (
    PaperIntegrityRepository,
    ResearchTrailRepository,
)
from opportunity.app.services.base import BaseService

AI_GATEWAY_URL = "http://localhost:8000/ai/chat"
SYSTEM_PROMPT = "你是论文诚信分析师，请判断这篇论文是否有撤稿、数据造假等诚信问题"


class PubpeerService(BaseService):
    def _call_llm(self, auth_header: str, prompt: str) -> str:
        req_body = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 2048,
        }
        req = urllib.request.Request(
            AI_GATEWAY_URL,
            data=json.dumps(req_body).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": auth_header},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
        envelope = json.loads(raw)
        data = envelope.get("data", {})
        return data.get("reply", "") if isinstance(data, dict) else str(data)

    def _parse_ai_reply(self, reply: str) -> dict:
        try:
            parsed = json.loads(reply)
            return {
                "integrity_score": parsed.get("integrity_score", 50),
                "retraction_warning": 1 if parsed.get("retraction_warning") else 0,
                "concerns": json.dumps(parsed.get("concerns", []), ensure_ascii=False),
                "flags": json.dumps(parsed.get("flags", []), ensure_ascii=False),
            }
        except (json.JSONDecodeError, TypeError):
            score = 30 if "撤稿" in reply or "造假" in reply else 50
            return {
                "integrity_score": score,
                "retraction_warning": 1 if "撤稿" in reply else 0,
                "concerns": json.dumps([reply[:200]], ensure_ascii=False),
                "flags": "[]",
            }

    def _check_or_get_cache(self, pubmed_id: Optional[str], doi: Optional[str]) -> Optional[dict]:
        if not pubmed_id and not doi:
            return None
        repo = PaperIntegrityRepository(self.db)
        if pubmed_id:
            row = repo.get_by_pubmed_id(pubmed_id)
        else:
            row = self.db.execute(
                "SELECT * FROM paper_integrity WHERE doi = ? AND is_active = 1 ORDER BY id DESC LIMIT 1",
                (doi,),
            ).fetchone()
        if not row:
            return None
        rec = dict(row)
        if rec.get("checked_at"):
            checked = datetime.fromisoformat(rec["checked_at"])
            if datetime.now(timezone.utc) - checked < timedelta(days=7):
                return rec
        return None

    def _do_check(
        self,
        auth_header: str,
        pubmed_id: Optional[str],
        doi: Optional[str],
        user_id: int,
    ) -> dict:
        prompt_parts = []
        if pubmed_id:
            prompt_parts.append(f"PubMed ID: {pubmed_id}")
        if doi:
            prompt_parts.append(f"DOI: {doi}")
        prompt = (
            '请分析以下论文的诚信状况，返回JSON格式：{"integrity_score": 0-100, "retraction_warning": bool, "concerns": ["..."], "flags": ["..."]}\n\n'
            + "\n".join(prompt_parts)
        )
        reply = self._call_llm(auth_header, prompt)
        result = self._parse_ai_reply(reply)
        now = datetime.now(timezone.utc).isoformat()
        repo = PaperIntegrityRepository(self.db)
        existing = None
        if pubmed_id:
            existing = repo.get_by_pubmed_id(pubmed_id)
        if not existing and doi:
            existing = self.db.execute(
                "SELECT id FROM paper_integrity WHERE doi = ? AND is_active = 1",
                (doi,),
            ).fetchone()
        if existing:
            self.db.execute(
                """UPDATE paper_integrity SET integrity_score=?, retraction_warning=?,
                   concerns=?, flags=?, checked_at=?, check_count=check_count+1,
                   updated_at=? WHERE id=?""",
                (
                    result["integrity_score"],
                    result["retraction_warning"],
                    result["concerns"],
                    result["flags"],
                    now,
                    now,
                    existing["id"],
                ),
            )
        else:
            repo.create(
                {
                    "pubmed_id": pubmed_id,
                    "doi": doi,
                    "integrity_score": result["integrity_score"],
                    "retraction_warning": result["retraction_warning"],
                    "concerns": result["concerns"],
                    "flags": result["flags"],
                    "checked_at": now,
                    "check_count": 1,
                    "created_by": user_id,
                    "created_at": now,
                    "updated_at": now,
                }
            )
        self.db.commit()
        return {
            "pubmed_id": pubmed_id,
            "doi": doi,
            "integrity_score": result["integrity_score"],
            "retraction_warning": bool(result["retraction_warning"]),
            "concerns": json.loads(result["concerns"]),
            "checked_at": now,
        }

    def check_trail_integrity(self, trail_id: int, auth_header: str, user_id: int) -> dict:
        repo = ResearchTrailRepository(self.db)
        trail = dict(repo.get_or_404(trail_id))
        cached = self._check_or_get_cache(trail.get("pubmed_id"), None)
        if cached:
            return {
                "pubmed_id": cached["pubmed_id"],
                "doi": cached.get("doi"),
                "integrity_score": cached["integrity_score"],
                "retraction_warning": bool(cached["retraction_warning"]),
                "concerns": json.loads(cached.get("concerns") or "[]"),
                "checked_at": cached["checked_at"],
            }
        return self._do_check(auth_header, trail.get("pubmed_id"), trail.get("doi"), user_id)

    def get_trail_integrity(self, trail_id: int) -> Optional[dict]:
        trail = dict(ResearchTrailRepository(self.db).get_or_404(trail_id))
        conditions = ["is_active = 1"]
        params: list = []
        if trail.get("pubmed_id"):
            conditions.append("pubmed_id = ?")
            params.append(trail["pubmed_id"])
        if trail.get("doi"):
            conditions.append("doi = ?")
            params.append(trail["doi"])
        if not params:
            return None
        where = " OR ".join(conditions)
        row = self.db.execute(
            f"SELECT * FROM paper_integrity WHERE {where} ORDER BY id DESC LIMIT 1",
            params,
        ).fetchone()
        return dict(row) if row else None

    def pubpeer_check(self, body, auth_header: str, user_id: int) -> dict | str:
        if not body.pubmed_id and not body.doi:
            return "validation_error"
        cached = self._check_or_get_cache(body.pubmed_id, body.doi)
        if cached:
            return {
                "pubmed_id": cached["pubmed_id"],
                "doi": cached.get("doi"),
                "integrity_score": cached["integrity_score"],
                "retraction_warning": bool(cached["retraction_warning"]),
                "concerns": json.loads(cached.get("concerns") or "[]"),
                "checked_at": cached["checked_at"],
            }
        return self._do_check(auth_header, body.pubmed_id, body.doi, user_id)

    def list_alerts(self, page: int, page_size: int) -> tuple:
        repo = PaperIntegrityRepository(self.db)
        return repo.paginate(
            page,
            page_size,
            conditions=[
                "(retraction_warning = 1 OR integrity_score < 50)",
                "is_active = 1",
            ],
            order_by="checked_at DESC",
        )
