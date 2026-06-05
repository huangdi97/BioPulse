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
from shared.base import PaginatedResponse


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


class IntelAnalyzerMixin:
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
