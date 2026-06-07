"""记忆门控服务，集成门控仓库配置阈值与保留策略实现记忆筛选，条目仓库与全息服务提供持久化存储与语义关联，评估服务基于内容特征自动评分排序，支撑高效精准的记忆召回。"""

import json
from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException
from starlette import status

from cloud.app.database import get_db
from cloud.app.repositories import (
    MemoryEntriesRepository,
    MemoryGatesRepository,
    MemoryRecallLogRepository,
)
from cloud.app.services.base import BaseService
from cloud.app.services.holographic_service import HolographicService
from cloud.app.services.memory_dashboard_service import MemoryDashboardService
from cloud.app.services.memory_evaluator_service import MemoryEvaluatorService


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class MemoryGateService(BaseService):
    def __init__(self, db=Depends(get_db), evaluator=None, dashboard_service=None, holographic_service=None, holographic_service_factory=None):
        super().__init__(db)
        self._evaluator = evaluator
        self._dashboard_service = dashboard_service
        self._holographic_service = holographic_service
        self._holographic_service_factory = holographic_service_factory

    @property
    def evaluator(self):
        if self._evaluator is None:
            self._evaluator = MemoryEvaluatorService(self.db)
        return self._evaluator

    @property
    def dashboard_service(self):
        if self._dashboard_service is None:
            self._dashboard_service = MemoryDashboardService(self.db)
        return self._dashboard_service

    @property
    def holographic_service(self):
        if self._holographic_service is None:
            factory = self._holographic_service_factory or HolographicService
            self._holographic_service = factory(self.db)
        return self._holographic_service

    def create_gate(
        self, name: str, source_type: str, importance_threshold: float = 0.5, ttl_days: int = 90, retention_policy: str = "normal"
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
        self.holographic_service.auto_associate(
            entry_id, {"context_tags": tags, "source_id": source_id or "", "memory_type": memory_type, "created_at": now}
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
        return repo.list_filtered(memory_type=memory_type, importance_min=importance_min, keyword=keyword, page=page, page_size=page_size)

    def get_entry(self, entry_id: int) -> dict:
        repo = MemoryEntriesRepository(self.db)
        row = repo.find_active_by_id(entry_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Entry not found")
        now = _now()
        repo.increment_access(entry_id, now)
        self.db.commit()
        return row

    def recall(self, query: str, memory_types: list[str], min_importance: float, max_results: int) -> dict:
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

    def auto_store(self, source_type: str, source_id: str, uid: int, auth_header: str = "") -> dict:
        return self.evaluator.auto_store(source_type=source_type, source_id=source_id, uid=uid, auth_header=auth_header)

    def dashboard(self) -> dict:
        return self.dashboard_service.dashboard()
