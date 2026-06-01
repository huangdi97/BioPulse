import json
import math
import urllib.error
import urllib.request
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, Request
from starlette import status

from cloud.app.repositories import (
    MarketIntelItemsRepository,
    MarketIntelSourcesRepository,
)
from cloud.app.services.base import BaseService
from shared.base import PaginatedResponse


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


def itd(row, parse_ai=False) -> dict:
    d = {
        "id": row["id"],
        "source_id": row["source_id"],
        "title": row["title"],
        "summary": row["summary"],
        "content": row["content"],
        "url": row["url"],
        "item_type": row["item_type"],
        "relevance_tags": json.loads(row["relevance_tags"]),
        "impact_level": row["impact_level"],
        "status": row["status"],
        "ai_analysis": row["ai_analysis"],
        "collected_at": row["collected_at"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
    if parse_ai and d["ai_analysis"]:
        try:
            d["ai_analysis"] = json.loads(d["ai_analysis"])
        except (json.JSONDecodeError, TypeError):
            pass
    return d


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


class MarketIntelService(BaseService):
    def create_source(self, name: str, source_type: str, target_keywords: list, user_id: int) -> dict:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sources_repo = MarketIntelSourcesRepository(self.db)
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
        sources_repo = MarketIntelSourcesRepository(self.db)
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
        sources_repo = MarketIntelSourcesRepository(self.db)
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
        sources_repo = MarketIntelSourcesRepository(self.db)
        items_repo = MarketIntelItemsRepository(self.db)
        existing = sources_repo.get_by_id(source_id)
        if not existing:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="market_intel_sources not found")
        items_repo.delete_by_source(source_id)
        sources_repo.delete(source_id)

    def collect_source(self, source_id: int, user_id: int) -> dict:
        sources_repo = MarketIntelSourcesRepository(self.db)
        items_repo = MarketIntelItemsRepository(self.db)
        src = sources_repo.get_by_id(source_id)
        if not src:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="market_intel_sources not found")
        _do_collect(items_repo, src, user_id)
        return {"collected_count": 3}

    def list_items(
        self,
        item_type: Optional[str] = None,
        status_filter: Optional[str] = None,
        impact_level: Optional[str] = None,
        keyword: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        items_repo = MarketIntelItemsRepository(self.db)
        conds, pars = [], []
        if item_type:
            conds.append("mi.item_type=?")
            pars.append(item_type)
        if status_filter:
            conds.append("mi.status=?")
            pars.append(status_filter)
        if impact_level:
            conds.append("mi.impact_level=?")
            pars.append(impact_level)
        if keyword:
            conds.append("(mi.title LIKE ? OR mi.summary LIKE ? OR mi.content LIKE ?)")
            lk = f"%{keyword}%"
            pars.extend([lk, lk, lk])
        if date_from:
            conds.append("mi.collected_at>=?")
            pars.append(date_from)
        if date_to:
            conds.append("mi.collected_at<=?")
            pars.append(date_to)
        total, rows = items_repo.list_with_source(
            conditions=conds or None,
            params=pars or None,
            page=page,
            page_size=page_size,
        )
        items = []
        for r in rows:
            d = itd(r)
            d["source_name"] = r.get("source_name")
            items.append(d)
        total_pages = math.ceil(total / max(page_size, 1))
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_item(self, item_id: int) -> dict:
        items_repo = MarketIntelItemsRepository(self.db)
        sources_repo = MarketIntelSourcesRepository(self.db)
        row = items_repo.get_by_id(item_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="market_intel_items not found")
        d = itd(row, parse_ai=True)
        src = sources_repo.get_by_id(row["source_id"])
        d["source_name"] = src["name"] if src else None
        return d

    def update_item_status(self, item_id: int, status_value: str) -> None:
        items_repo = MarketIntelItemsRepository(self.db)
        existing = items_repo.get_by_id(item_id)
        if not existing:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="market_intel_items not found")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        items_repo.update_fields(item_id, {"status": status_value, "updated_at": now})

    def analyze_item(self, item_id: int, request: Request) -> dict:
        items_repo = MarketIntelItemsRepository(self.db)
        row = items_repo.get_by_id(item_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="market_intel_items not found")
        prompt = (
            f"请对以下市场情报进行深度分析，输出JSON格式：\n"
            f"标题：{row['title']}\n摘要：{row['summary']}\n内容：{row['content']}\n"
            f"影响级别：{row['impact_level']}\n请分析：1)关键要点 2)商业影响 3)建议行动 4)相关风险"
        )
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a market intelligence analyst. Output analysis in JSON format.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 1024,
        }
        req = urllib.request.Request(
            "http://localhost:8000/ai/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": request.headers.get("Authorization", ""),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as rp:
                resp = json.loads(rp.read().decode("utf-8"))
                ai_result = resp.get("data", {}).get("reply", "")
        except Exception as e:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=f"AI analysis failed: {str(e)}")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        items_repo.update_fields(
            item_id,
            {
                "ai_analysis": json.dumps(ai_result, ensure_ascii=False),
                "updated_at": now,
            },
        )
        return {"analysis": ai_result}

    def collect_all(self, user_id: int) -> dict:
        sources_repo = MarketIntelSourcesRepository(self.db)
        items_repo = MarketIntelItemsRepository(self.db)
        sources = sources_repo.list_active()
        for src in sources:
            _do_collect(items_repo, src, user_id)
        return {"collected_count": len(sources) * 3, "sources_processed": len(sources)}

    def dashboard(self) -> dict:
        items_repo = MarketIntelItemsRepository(self.db)
        t = items_repo.count()
        u = items_repo.count(conditions=["status='unread'"])
        bt = items_repo.count_by_field("item_type")
        bi = items_repo.count_by_field("impact_level")
        rc = [itd(r) for r in items_repo.count_recent_critical()]
        td = items_repo.count_by_date_range(6)
        return {
            "total_items": t,
            "unread_count": u,
            "by_type": bt,
            "by_impact": bi,
            "recent_critical": rc,
            "trend_7d": td,
        }
