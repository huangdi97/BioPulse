import json
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    RouteRulesRepository,
    RouteLogsRepository,
    RouteStatsRepository,
    AgentRolesRepository,
)
from cloud.app.services.base import BaseService
from shared.base import validate_columns
from shared.columns import TABLE_ROUTE_RULES_COLS
from shared.config import settings

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
TIMEOUT_SECONDS = 30


def _call_deepseek(messages: list, temperature: float, max_tokens: int) -> dict:
    api_key = settings.deepseek_api_key
    if not api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DEEPSEEK_API_KEY not configured",
        )
    req_body = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    req_data = json.dumps(req_body).encode("utf-8")
    req = urllib.request.Request(
        DEEPSEEK_URL,
        data=req_data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            raw = resp.read()
    except urllib.error.URLError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, detail=f"DeepSeek API call failed: {exc}"
        )
    payload = json.loads(raw)
    choices = payload.get("choices", [])
    reply = choices[0].get("message", {}).get("content", "") if choices else ""
    return {"reply": reply, "usage": payload.get("usage", {})}


class RouteService(BaseService):
    def create_rule(
        self,
        name: str,
        priority: int,
        condition_field: str,
        condition_operator: str,
        condition_value: str,
        target_role_id: int,
        fallback_role_id: Optional[int],
        max_tokens: int,
        temperature: float,
        created_by: int,
    ) -> dict:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rules_repo = RouteRulesRepository(self.db)
        rule_id = rules_repo.create(
            {
                "name": name,
                "priority": priority,
                "condition_field": condition_field,
                "condition_operator": condition_operator,
                "condition_value": condition_value,
                "target_role_id": target_role_id,
                "fallback_role_id": fallback_role_id,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "created_by": created_by,
                "created_at": now,
                "updated_at": now,
            }
        )
        return rules_repo.get_by_id(rule_id)

    def list_rules(self) -> list:
        rules_repo = RouteRulesRepository(self.db)
        return rules_repo.list_all_ordered()

    def update_rule(
        self,
        rule_id: int,
        name: Optional[str] = None,
        priority: Optional[int] = None,
        condition_value: Optional[str] = None,
        target_role_id: Optional[int] = None,
        is_active: Optional[int] = None,
    ) -> dict:
        rules_repo = RouteRulesRepository(self.db)
        existing = rules_repo.get_by_id(rule_id)
        if not existing:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Rule not found")
        updates = {}
        for f in ["name", "priority", "condition_value", "target_role_id", "is_active"]:
            v = locals().get(f)
            if v is not None:
                updates[f] = v
        if updates:
            updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            validate_columns(updates, "route_rules", TABLE_ROUTE_RULES_COLS)
            rules_repo.update(rule_id, updates)
        return rules_repo.get_by_id(rule_id)

    def delete_rule(self, rule_id: int) -> None:
        rules_repo = RouteRulesRepository(self.db)
        existing = rules_repo.get_by_id(rule_id)
        if not existing:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Rule not found")
        rules_repo.delete(rule_id)

    def execute_route(self, input_text: str, uid: int, source: str) -> dict:
        start = time.time()
        rules_repo = RouteRulesRepository(self.db)
        logs_repo = RouteLogsRepository(self.db)
        stats_repo = RouteStatsRepository(self.db)
        roles_repo = AgentRolesRepository(self.db)
        rules = rules_repo.list_active_ordered()
        matched = None
        for r in rules:
            cv = r["condition_value"]
            op = r["condition_operator"]
            if op == "contains":
                if cv and cv in input_text:
                    matched = r
                    break
                elif not cv:
                    matched = r
                    break
            elif op == "equals":
                if input_text == cv:
                    matched = r
                    break
            elif op == "starts_with":
                if input_text.startswith(cv):
                    matched = r
                    break
        if matched is None:
            latency_ms = int((time.time() - start) * 1000)
            return {
                "role_name": "",
                "response": "No matching rule found.",
                "confidence": 0.0,
                "latency_ms": latency_ms,
                "matched_rule": None,
            }
        role_id = matched["target_role_id"]
        confidence = 0.90
        role_row = roles_repo.get_by_id(role_id)
        role_name = role_row["name"] if role_row else "Unknown"
        system_prompt = role_row["system_prompt"] if role_row else ""
        temperature = matched["temperature"] or 0.7
        max_tokens = matched["max_tokens"] or 2048
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": input_text})
        ai_result = _call_deepseek(messages, temperature, max_tokens)
        reply = ai_result["reply"]
        usage = ai_result.get("usage", {})
        tokens_used = usage.get("total_tokens", 0)
        latency_ms = int((time.time() - start) * 1000)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logs_repo.create(
            {
                "input_text": input_text,
                "matched_rule_id": matched["id"],
                "matched_rule_name": matched["name"],
                "assigned_role_id": role_id,
                "assigned_role_name": role_name,
                "confidence": confidence,
                "response_summary": reply[:500],
                "tokens_used": tokens_used,
                "latency_ms": latency_ms,
                "source": source,
                "created_by": uid,
                "created_at": now,
            }
        )
        stats_repo.upsert(role_id, latency_ms, tokens_used, confidence)
        return {
            "role_name": role_name,
            "response": reply,
            "confidence": confidence,
            "latency_ms": latency_ms,
            "matched_rule": matched,
        }

    def list_logs(
        self,
        role_id: Optional[int] = None,
        source: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        logs_repo = RouteLogsRepository(self.db)
        total, total_pages, items = logs_repo.list_filtered(
            role_id=role_id,
            source=source,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_log(self, log_id: int) -> dict:
        logs_repo = RouteLogsRepository(self.db)
        row = logs_repo.get_by_id(log_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Log not found")
        return row

    def get_stats(self) -> list:
        stats_repo = RouteStatsRepository(self.db)
        return stats_repo.list_with_role_name()

    def get_dashboard(self) -> dict:
        logs_repo = RouteLogsRepository(self.db)
        total = logs_repo.count()
        if total == 0:
            return {
                "total_executions": 0,
                "role_distribution": [],
                "avg_latency_ms": 0,
                "recent_logs": [],
            }
        rows = logs_repo.role_distribution()
        role_dist = [
            {
                "role_id": r["assigned_role_id"],
                "role_name": r["assigned_role_name"],
                "count": r["cnt"],
                "percentage": round(r["cnt"] / total * 100, 2),
            }
            for r in rows
        ]
        avg_lat = logs_repo.avg_latency()
        recent = logs_repo.list_recent(10)
        return {
            "total_executions": total,
            "role_distribution": role_dist,
            "avg_latency_ms": round(avg_lat, 2),
            "recent_logs": recent,
        }
