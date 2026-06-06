"""记忆门控服务，负责记忆条目的重要性评估与路由分发。"""

import json
import urllib.request
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    ComplianceAuditRecordsRepository,
    CrossCaseInsightsRepository,
    DecisionCasesRepository,
    MemoryEntriesRepository,
    MemoryGatesRepository,
    MemoryRecallLogRepository,
)
from cloud.app.services.base import BaseService


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class MemoryGateService(BaseService):
    """记忆门控服务，提供记忆门的创建、条目的评分过滤与路由。"""

    def _call_ai(self, messages: list[dict], auth_header: str) -> dict:
        payload = {"messages": messages, "temperature": 0.3, "max_tokens": 256}
        req = urllib.request.Request(
            "http://localhost:8000/ai/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": auth_header},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as rp:
            return json.loads(rp.read().decode("utf-8")).get("data", {})

    def create_gate(
        self,
        name: str,
        source_type: str,
        importance_threshold: float = 0.5,
        ttl_days: int = 90,
        retention_policy: str = "normal",
    ) -> dict:
        repo = MemoryGatesRepository(self.db)
        gate_id = repo.create(
            {
                "name": name,
                "source_type": source_type,
                "importance_threshold": importance_threshold,
                "ttl_days": ttl_days,
                "retention_policy": retention_policy,
                "created_at": _now(),
            }
        )
        return {
            "id": gate_id,
            "name": name,
            "source_type": source_type,
            "importance_threshold": importance_threshold,
            "ttl_days": ttl_days,
            "retention_policy": retention_policy,
        }

    def list_gates(self) -> list[dict]:
        repo = MemoryGatesRepository(self.db)
        return repo.list_ordered()

    def create_entry(
        self,
        title: str,
        content: str,
        memory_type: str,
        source_type: str,
        source_id: Optional[str],
        importance: float,
        context_tags: list[str],
        uid: int,
    ) -> dict:
        repo = MemoryEntriesRepository(self.db)
        now = _now()
        tags = json.dumps(context_tags, ensure_ascii=False)
        entry_id = repo.create(
            {
                "title": title,
                "content": content,
                "memory_type": memory_type,
                "source_type": source_type,
                "source_id": source_id or "",
                "importance": importance,
                "context_tags": tags,
                "access_count": 0,
                "created_by": uid,
                "created_at": now,
                "updated_at": now,
            }
        )
        return {
            "id": entry_id,
            "title": title,
            "content": content,
            "memory_type": memory_type,
            "source_type": source_type,
            "source_id": source_id,
            "importance": importance,
            "context_tags": context_tags,
        }

    def list_entries(
        self,
        memory_type: Optional[str] = None,
        importance_min: Optional[float] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[int, int, list[dict]]:
        repo = MemoryEntriesRepository(self.db)
        return repo.list_filtered(
            memory_type=memory_type,
            importance_min=importance_min,
            keyword=keyword,
            page=page,
            page_size=page_size,
        )

    def get_entry(self, entry_id: int) -> dict:
        repo = MemoryEntriesRepository(self.db)
        row = repo.find_active_by_id(entry_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Entry not found")
        now = _now()
        repo.increment_access(entry_id, now)
        self.db.commit()
        return row

    def recall(
        self,
        query: str,
        memory_types: list[str],
        min_importance: float,
        max_results: int,
    ) -> dict:
        entry_repo = MemoryEntriesRepository(self.db)
        recall_repo = MemoryRecallLogRepository(self.db)

        conditions, params = ["is_active = 1", "importance >= ?"], [min_importance]
        if memory_types:
            placeholders = ",".join("?" for _ in memory_types)
            conditions.append(f"memory_type IN ({placeholders})")
            params.extend(memory_types)
        where = " WHERE " + " AND ".join(conditions)
        rows = entry_repo.db.execute(
            f"SELECT id, title, content, memory_type, importance, context_tags FROM {entry_repo.table_name}{where} ORDER BY importance DESC LIMIT ?",
            params + [max_results],
        ).fetchall()
        results = [dict(r) for r in rows]
        ids = [r["id"] for r in rows]
        now = _now()
        recall_repo.create(
            {
                "query_text": query,
                "memory_ids": json.dumps(ids),
                "result_count": len(results),
                "context": json.dumps({"memory_types": memory_types}, ensure_ascii=False),
                "created_at": now,
            }
        )
        return {"results": results, "recall_count": len(results)}

    def auto_store(self, source_type: str, source_id: str, uid: int, auth_header: str) -> dict:
        gate_repo = MemoryGatesRepository(self.db)
        entry_repo = MemoryEntriesRepository(self.db)

        gate = gate_repo.find_active_by_source_type(source_type)
        if not gate:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=f"No active gate for source_type '{source_type}'",
            )

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
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=f"Source {source_type}/{source_id} not found",
            )

        messages = [
            {
                "role": "system",
                "content": "判断这条信息的重要性，给出0到1之间的一个分数（只输出数字，不要任何其他文字）。",
            },
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
                return {
                    "stored": False,
                    "importance": importance,
                    "reason": "Already stored",
                }
            now = _now()
            tags = json.dumps([source_type], ensure_ascii=False)
            entry_repo.create(
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

        return {"stored": stored, "importance": importance}

    def dashboard(self) -> dict:
        entry_repo = MemoryEntriesRepository(self.db)
        recall_repo = MemoryRecallLogRepository(self.db)

        total = entry_repo.count_active()
        type_rows = entry_repo.by_type_stats()
        by_type = [
            {
                "memory_type": r["memory_type"],
                "count": r["cnt"],
                "avg_importance": round(r["avg_imp"], 4),
            }
            for r in type_rows
        ]

        tag_counter = {}
        entries = entry_repo.all_context_tags_active()
        for e in entries:
            try:
                tags = json.loads(e["context_tags"])
            except (json.JSONDecodeError, TypeError):
                tags = []
            for t in tags:
                tag_counter[t] = tag_counter.get(t, 0) + 1
        top_tags = sorted(tag_counter.items(), key=lambda x: x[1], reverse=True)[:10]
        top_tags = [{"tag": t, "count": c} for t, c in top_tags]

        recent_logs = recall_repo.list_recent(limit=5)

        return {
            "total_entries": total,
            "by_memory_type": by_type,
            "top_context_tags": top_tags,
            "recent_recall_logs": recent_logs,
        }
