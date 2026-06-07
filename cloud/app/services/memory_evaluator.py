"""记忆门控 AI 调用、来源加载与重要性评分 mixin。"""

import json
import urllib.request
from datetime import datetime

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    ComplianceAuditRecordsRepository,
    CrossCaseInsightsRepository,
    DecisionCasesRepository,
    MemoryEntriesRepository,
    MemoryGatesRepository,
)
from cloud.app.services.holographic_service import HolographicService
from shared.config import settings as config_settings


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class MemoryEvaluatorMixin:
    def _call_ai(self, messages: list[dict], auth_header: str) -> dict:
        payload = {"messages": messages, "temperature": 0.3, "max_tokens": 256}
        req = urllib.request.Request(
            f"{config_settings.ai_chat_url}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": auth_header},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as rp:
            return json.loads(rp.read().decode("utf-8")).get("data", {})

    def auto_store(self, source_type: str, source_id: str, uid: int, auth_header: str) -> dict:
        gate_repo = MemoryGatesRepository(self.db)
        entry_repo = MemoryEntriesRepository(self.db)
        gate = gate_repo.find_active_by_source_type(source_type)
        if not gate:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"No active gate for source_type '{source_type}'")
        source_data = None
        source_title = ""
        source_content = ""
        if source_type == "insight":
            repo = CrossCaseInsightsRepository(self.db)
            row = repo.get_by_id(int(source_id))
            if row:
                source_title = row.get("title", "")
                source_content = f"Type: {row.get('insight_type', '')}. Summary: {row.get('summary', '')}. Detail: {row.get('detail', '')}"
                source_data = row
        elif source_type == "case":
            repo = DecisionCasesRepository(self.db)
            row = repo.get_by_id(int(source_id))
            if row:
                source_title = row.get("name", "")
                source_content = f"Description: {row.get('description', '')}. Outcome: {row.get('outcome', '')}. Score: {row.get('outcome_score', 0)}"
                source_data = row
        elif source_type == "compliance":
            repo = ComplianceAuditRecordsRepository(self.db)
            row = repo.get_by_id(int(source_id))
            if row:
                source_title = row.get("content", "")[:100]
                source_content = f"Content: {row.get('content', '')}. Risk: {row.get('risk_level', '')}. Score: {row.get('score', 0)}. Passed: {row.get('passed', 0)}"
                source_data = row
        if not source_data:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Source {source_type}/{source_id} not found")
        messages = [
            {"role": "system", "content": "判断这条信息的重要性，给出0到1之间的一个分数（只输出数字，不要任何其他文字）。"},
            {"role": "user", "content": source_content},
        ]
        try:
            ai_resp = self._call_ai(messages, auth_header)
        except Exception:
            return {"stored": False, "importance": 0, "error": "AI call failed"}
        raw = ai_resp.get("reply", "0")
        try:
            importance = float(raw.strip())
            importance = max(0.0, min(1.0, importance))
        except (ValueError, TypeError):
            importance = 0.0
        stored = importance >= gate["importance_threshold"]
        if stored:
            existing = entry_repo.find_by_source_active(source_type, source_id)
            if existing:
                return {"stored": False, "importance": importance, "reason": "Already stored"}
            now = _now()
            tags = json.dumps([source_type], ensure_ascii=False)
            entry_id = entry_repo.create(
                {
                    "title": source_title,
                    "content": source_content,
                    "memory_type": source_type,
                    "source_type": source_type,
                    "source_id": source_id,
                    "importance": importance,
                    "context_tags": tags,
                    "access_count": 0,
                    "created_by": uid,
                    "created_at": now,
                    "updated_at": now,
                }
            )
            HolographicService(self.db).auto_associate(
                entry_id, {"context_tags": tags, "source_id": source_id, "memory_type": source_type, "created_at": now}
            )
        return {"stored": stored, "importance": importance}
