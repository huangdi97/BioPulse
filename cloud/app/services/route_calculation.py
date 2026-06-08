"""路由执行计算方法。"""

import json
import time
import urllib.error
import urllib.request
from datetime import datetime

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import AgentRolesRepository, RouteLogsRepository, RouteRulesRepository, RouteStatsRepository
from shared.config import settings

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
TIMEOUT_SECONDS = 30


def _call_deepseek(messages: list, temperature: float, max_tokens: int) -> dict:
    """调用 DeepSeek API 发送对话并返回回复内容。

    Args:
        messages: 对话消息列表
        temperature: 温度参数
        max_tokens: 最大 token 数

    Returns:
        含 reply 和 usage 的字典
    """
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
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=f"DeepSeek API call failed: {exc}")
    payload = json.loads(raw)
    choices = payload.get("choices", [])
    reply = choices[0].get("message", {}).get("content", "") if choices else ""
    return {"reply": reply, "usage": payload.get("usage", {})}


class RouteCalculationMixin:
    """路由规则匹配、AI 调用和执行日志写入方法。"""

    def execute_route(self, input_text: str, uid: int, source: str) -> dict:
        """根据输入文本匹配路由规则并调用 DeepSeek AI 执行调度。

        Args:
            input_text: 用户输入文本
            uid: 用户 ID
            source: 来源标识

        Returns:
            包含角色名称、AI 回复、置信度、延迟及匹配规则信息的字典
        """
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
