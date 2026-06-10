"""HCP 行为模拟核心逻辑。"""

import json
import urllib.error
import urllib.request
from collections.abc import Callable

from fastapi import HTTPException
from starlette import status

from shared.config import settings

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
TIMEOUT_SECONDS = 30

DEFAULT_RESULT = {
    "expected_outcome": "",
    "confidence": 0.5,
    "suggested_approach": "",
    "key_concerns": "",
    "recommended_topics": "",
    "risk_factors": "",
}


def _call_ai(system_prompt: str, user_prompt: str) -> str:
    api_key = settings.deepseek_api_key
    if not api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DEEPSEEK_API_KEY not configured",
        )
    req_body = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
    }
    req = urllib.request.Request(
        DEEPSEEK_URL,
        data=json.dumps(req_body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            payload = json.loads(resp.read())
    except urllib.error.URLError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=f"AI call failed: {exc}")
    choices = payload.get("choices", [])
    return choices[0].get("message", {}).get("content", "") if choices else ""


def build_simulation_prompts(hcp_row: dict, int_rows: list[dict], scenario: str, strategy: str) -> tuple[str, str]:
    system_prompt = "你是一名HCP行为模拟专家。请基于HCP档案和历史互动记录，模拟该HCP在给定场景下的行为反应。以JSON格式输出："
    user_prompt = (
        f"HCP档案：\n{json.dumps(hcp_row, ensure_ascii=False, indent=2)}\n\n"
        f"最近互动：\n{json.dumps(int_rows, ensure_ascii=False, indent=2)}\n\n"
        f"场景：{scenario}\n策略：{strategy or '默认策略'}\n\n"
        '{"expected_outcome":"...","confidence":0.5,"suggested_approach":"...",'
        '"key_concerns":"...","recommended_topics":"...","risk_factors":"..."}'
    )
    return system_prompt, user_prompt


def simulate_hcp_response(
    hcp_row: dict,
    int_rows: list[dict],
    scenario: str,
    strategy: str,
    call_ai: Callable[[str, str], str] = _call_ai,
) -> dict:
    system_prompt, user_prompt = build_simulation_prompts(hcp_row, int_rows, scenario, strategy)
    try:
        ai_raw = call_ai(system_prompt, user_prompt)
        result = json.loads(ai_raw)
    except json.JSONDecodeError:
        result = DEFAULT_RESULT.copy()
    return result


def build_simulation_record(
    hcp_id: int,
    hcp_row: dict,
    int_rows: list[dict],
    scenario: str,
    strategy: str,
    user_id: int,
    call_ai: Callable[[str, str], str] = _call_ai,
) -> dict:
    result = simulate_hcp_response(hcp_row, int_rows, scenario, strategy, call_ai=call_ai)
    sim_data = json.dumps(
        {"scenario": scenario, "strategy": strategy, "profile_id": hcp_id},
        ensure_ascii=False,
    )
    return {
        "hcp_id": hcp_id,
        "scenario": scenario,
        "strategy": strategy,
        "expected_outcome": result.get("expected_outcome", ""),
        "confidence": result.get("confidence", 0.5),
        "suggested_approach": result.get("suggested_approach", ""),
        "key_concerns": result.get("key_concerns", ""),
        "recommended_topics": result.get("recommended_topics", ""),
        "risk_factors": result.get("risk_factors", ""),
        "simulation_data": sim_data,
        "status": "completed",
        "created_by": user_id,
    }
