"""教练服务：话术提示管理、AI教练建议与辅导会话。"""

import json
import logging
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Optional

from sales_assistant.app.repositories import PromptRepository, SessionRepository
from sales_assistant.app.services.base import BaseService

AI_GATEWAY_URL = "http://localhost:8000/ai/chat"
TIMEOUT_SECONDS = 30
logger = logging.getLogger(__name__)


class CoachService(BaseService):
    """教练服务：管理销售话术模板、生成AI教练建议、跟踪辅导会话。"""

    def create_prompt(self, body, user_id: int) -> int:
        repo = PromptRepository(self.db)
        data = body.model_dump()
        now = datetime.now(timezone.utc).isoformat()
        data["created_by"] = user_id
        data["created_at"] = now
        data["updated_at"] = now
        return repo.create(data)

    def list_prompts(
        self,
        page: int,
        page_size: int,
        scenario: Optional[str] = None,
        category: Optional[str] = None,
    ) -> tuple:
        repo = PromptRepository(self.db)
        conditions = ["is_active = 1"]
        params: list = []
        if scenario:
            conditions.append("scenario LIKE ?")
            params.append(f"%{scenario}%")
        if category:
            conditions.append("category LIKE ?")
            params.append(f"%{category}%")
        return repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params,
            order_by="priority DESC, id DESC",
        )

    def update_prompt(self, prompt_id: int, body) -> dict:
        repo = PromptRepository(self.db)
        repo.get_or_404(prompt_id)
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(repo.get_by_id(prompt_id))
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(prompt_id, updates)
        return dict(repo.get_by_id(prompt_id))

    def delete_prompt(self, prompt_id: int) -> None:
        repo = PromptRepository(self.db)
        repo.get_or_404(prompt_id)
        repo.soft_delete(prompt_id)

    def coach_suggest(self, body) -> dict:
        repo = PromptRepository(self.db)
        rows = repo.list_all(
            conditions=["is_active = 1", "scenario LIKE ?"],
            params=[f"%{body.scenario}%"],
            order_by="priority DESC",
        )
        rows = rows[:3]
        if rows:
            suggestions = [
                {
                    "prompt_id": r["id"],
                    "title": r["scenario"],
                    "content": r["prompt_template"],
                    "priority": r["priority"],
                }
                for r in rows
            ]
            return {"suggestions": suggestions}

        system_prompt = '你是一位资深销售教练，根据场景生成话术建议。回复JSON：{"suggestions":[{"title":"...","content":"...","priority":5}]}'
        user_parts = [f"场景：{body.scenario}"]
        if body.hcp_name:
            user_parts.append(f"客户：{body.hcp_name}")
        if body.product_name:
            user_parts.append(f"产品：{body.product_name}")
        if body.recent_context:
            user_parts.append(f"背景：{body.recent_context}")
        if body.hcp_tier:
            user_parts.append(f"级别：{body.hcp_tier}")
        user_parts.append("请生成3条话术建议。")

        req_body = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "\n".join(user_parts)},
            ],
            "temperature": 0.7,
            "max_tokens": 2048,
        }
        try:
            req_data = json.dumps(req_body).encode("utf-8")
            req = urllib.request.Request(
                AI_GATEWAY_URL,
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                raw = resp.read()
            envelope = json.loads(raw)
            reply = envelope.get("data", {}).get("reply", "")
            if reply:
                parsed = json.loads(reply)
                return parsed
        except Exception as exc:
            logger.warning("AI suggest fallback: %s", exc)
        return {"suggestions": []}

    def create_session(self, body, user_id: int) -> int:
        repo = SessionRepository(self.db)
        data = body.model_dump()
        now = datetime.now(timezone.utc).isoformat()
        data["started_at"] = now
        data["created_by"] = user_id
        data["created_at"] = now
        return repo.create(data)

    def list_sessions(self, page: int, page_size: int) -> tuple:
        repo = SessionRepository(self.db)
        return repo.paginate(
            page=page,
            page_size=page_size,
            order_by="created_at DESC",
        )

    def update_session(self, session_id: int, body) -> dict:
        repo = SessionRepository(self.db)
        repo.get_or_404(session_id)
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(repo.get_by_id(session_id))
        repo.update(session_id, updates)
        return dict(repo.get_by_id(session_id))
