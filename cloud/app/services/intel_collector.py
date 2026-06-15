"""情报采集模块，负责市场情报源的创建与模拟采集。"""

import json
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    MarketIntelItemsRepository,
    MarketIntelSourcesRepository,
)


def sd(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "source_type": row["source_type"],
        "target_keywords": json.loads(row["target_keywords"]),
        "is_active": row["is_active"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _sim(src_name, kw, idx):
    return (
        f"【{src_name}】关键词「{kw}」相关情报第{idx}条",
        f"关于{kw}的最新动态摘要第{idx}条",
        f"详细内容：这是模拟采集到的第{idx}条情报信息。",
    )


def _do_collect(repo, src, user_id):
    keywords = json.loads(src["target_keywords"])
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for i in range(3):
        kw = keywords[i % len(keywords)] if keywords else "综合"
        title, summary, content = _sim(src["name"], kw, i + 1)
        repo.create_raw(
            {
                "source_id": src["id"],
                "title": title,
                "summary": summary,
                "content": content,
                "item_type": src["source_type"],
                "impact_level": ["low", "medium", "high"][i % 3],
                "status": "unread",
                "collected_at": now,
                "created_by": user_id,
                "created_at": now,
                "updated_at": now,
            }
        )


class IntelCollectorMixin:
    """情报采集混入类，提供情报源的创建、列表查询与采集操作。"""

    def create_source(self, name: str, source_type: str, target_keywords: list, user_id: int) -> dict:
        """创建新的情报源。"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sources_repo = MarketIntelSourcesRepository(self._connection())
        row_id = sources_repo.create(
            {
                "name": name,
                "source_type": source_type,
                "target_keywords": json.dumps(target_keywords, ensure_ascii=False),
                "created_by": user_id,
                "created_at": now,
                "updated_at": now,
            }
        )
        row = sources_repo.get_by_id(row_id)
        return sd(row)

    def list_sources(self, source_type: Optional[str] = None, is_active: Optional[int] = None) -> list:
        """查询情报源列表，支持按类型和状态过滤。"""
        sources_repo = MarketIntelSourcesRepository(self._connection())
        conditions, params = [], []
        if source_type:
            conditions.append("source_type=?")
            params.append(source_type)
        if is_active is not None:
            conditions.append("is_active=?")
            params.append(is_active)
        rows = sources_repo.list_all(
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )
        return [sd(r) for r in rows]

    def update_source(
        self,
        source_id: int,
        name: Optional[str] = None,
        source_type: Optional[str] = None,
        target_keywords: Optional[list] = None,
        is_active: Optional[int] = None,
    ) -> dict:
        """更新情报源的字段信息。"""
        sources_repo = MarketIntelSourcesRepository(self._connection())
        existing = sources_repo.get_by_id(source_id)
        if not existing:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="market_intel_sources not found")
        updates = {}
        if name is not None:
            updates["name"] = name
        if source_type is not None:
            updates["source_type"] = source_type
        if target_keywords is not None:
            updates["target_keywords"] = json.dumps(target_keywords, ensure_ascii=False)
        if is_active is not None:
            updates["is_active"] = is_active
        if updates:
            updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sources_repo.update_fields(source_id, updates)
        row = sources_repo.get_by_id(source_id)
        return sd(row)

    def delete_source(self, source_id: int) -> None:
        """删除指定情报源及其关联的情报条目。"""
        sources_repo = MarketIntelSourcesRepository(self._connection())
        items_repo = MarketIntelItemsRepository(self._connection())
        existing = sources_repo.get_by_id(source_id)
        if not existing:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="market_intel_sources not found")
        items_repo.delete_by_source(source_id)
        sources_repo.delete(source_id)

    def collect_source(self, source_id: int, user_id: int) -> dict:
        """采集指定情报源的模拟情报数据。"""
        sources_repo = MarketIntelSourcesRepository(self._connection())
        items_repo = MarketIntelItemsRepository(self._connection())
        src = sources_repo.get_by_id(source_id)
        if not src:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="market_intel_sources not found")
        _do_collect(items_repo, src, user_id)
        return {"collected_count": 3}

    def collect_all(self, user_id: int) -> dict:
        """采集所有活跃情报源的模拟情报数据。"""
        sources_repo = MarketIntelSourcesRepository(self._connection())
        items_repo = MarketIntelItemsRepository(self._connection())
        sources = sources_repo.list_active()
        for src in sources:
            _do_collect(items_repo, src, user_id)
        return {"collected_count": len(sources) * 3, "sources_processed": len(sources)}
