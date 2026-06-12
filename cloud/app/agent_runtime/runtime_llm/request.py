"""LLM request building and raw HTTP callers."""

import logging
import os

import httpx

from cloud.app.agent_runtime.secret_manager import SecretManager
from shared.ai_gateway import LLM_INFERENCE_TIMEOUT
from shared.config import settings as config_settings

logger = logging.getLogger(__name__)


def raw_llm_call(request_body: dict, auth_header: str) -> dict:
    with httpx.Client(timeout=LLM_INFERENCE_TIMEOUT) as client:
        resp = client.post(
            f"{config_settings.ai_chat_url}",
            json=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": auth_header,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def raw_llm_call_async(request_body: dict, auth_header: str) -> dict:
    async with httpx.AsyncClient(timeout=LLM_INFERENCE_TIMEOUT) as client:
        resp = await client.post(
            f"{config_settings.ai_chat_url}",
            json=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": auth_header,
            },
        )
        resp.raise_for_status()
        return resp.json()


def build_cloud_body(messages: list[dict], temperature: float, agent_mode: bool = False) -> dict:
    body = {
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2048,
    }
    if agent_mode:
        body["agent_mode"] = True
    return body


def call_local(config, messages: list[dict], temperature: float, fallback_fn) -> dict:
    prompt_text = "\n\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages)
    body = {
        "model": config.ai_local_model,
        "prompt": prompt_text,
        "stream": False,
        "options": {"temperature": temperature},
    }
    try:
        with httpx.Client(timeout=LLM_INFERENCE_TIMEOUT) as client:
            resp = client.post(
                config.ai_local_endpoint,
                json=body,
            )
            raw = resp.json()
    except Exception as e:
        logger.warning("Local model call failed, fallback to Cloud Normal: %s", e)
        result = fallback_fn()
        result["model_tier"] = "cloud_normal"
        return result

    normalized = {
        "data": {
            "reply": raw.get("response", ""),
            "usage": {
                "prompt_tokens": raw.get("prompt_eval_count", 0),
                "completion_tokens": raw.get("eval_count", 0),
                "total_tokens": raw.get("prompt_eval_count", 0) + raw.get("eval_count", 0),
            },
        }
    }
    return {"success": True, "data": normalized, "attempts": 1}


async def call_local_async(config, messages: list[dict], temperature: float, fallback_fn) -> dict:
    prompt_text = "\n\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages)
    body = {
        "model": config.ai_local_model,
        "prompt": prompt_text,
        "stream": False,
        "options": {"temperature": temperature},
    }
    try:
        async with httpx.AsyncClient(timeout=LLM_INFERENCE_TIMEOUT) as client:
            resp = await client.post(
                config.ai_local_endpoint,
                json=body,
            )
            raw = resp.json()
    except Exception as e:
        logger.warning("Local model call failed, fallback to Cloud Normal: %s", e)
        result = await fallback_fn()
        result["model_tier"] = "cloud_normal"
        return result

    normalized = {
        "data": {
            "reply": raw.get("response", ""),
            "usage": {
                "prompt_tokens": raw.get("prompt_eval_count", 0),
                "completion_tokens": raw.get("eval_count", 0),
                "total_tokens": raw.get("prompt_eval_count", 0) + raw.get("eval_count", 0),
            },
        }
    }
    return {"success": True, "data": normalized, "attempts": 1}


def call_provider(messages: list[dict], temperature: float, provider: dict) -> dict:
    _secret_mgr = SecretManager()
    api_key = _secret_mgr.get(provider["env_key"]) or os.environ.get(provider["env_key"], "")
    if not api_key:
        logger.warning("Provider %s has no API key configured, skipping", provider["provider"])
        return {"success": False, "data": None, "error": f"No API key for {provider['provider']}", "attempts": 1}
    body = {
        "model": provider["model"],
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2048,
    }
    try:
        with httpx.Client(timeout=LLM_INFERENCE_TIMEOUT) as client:
            resp = client.post(
                provider["url"],
                json=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
            )
            raw = resp.json()
    except Exception as exc:
        return {"success": False, "data": None, "error": str(exc), "attempts": 1}
    choices = raw.get("choices", [])
    reply = ""
    if choices:
        reply = choices[0].get("message", {}).get("content", "")
    usage = raw.get("usage", {})
    return {
        "success": True,
        "data": {"data": {"reply": reply, "usage": usage}},
        "attempts": 1,
    }


async def call_provider_async(messages: list[dict], temperature: float, provider: dict) -> dict:
    _secret_mgr = SecretManager()
    api_key = _secret_mgr.get(provider["env_key"]) or os.environ.get(provider["env_key"], "")
    if not api_key:
        logger.warning("Provider %s has no API key configured, skipping", provider["provider"])
        return {"success": False, "data": None, "error": f"No API key for {provider['provider']}", "attempts": 1}
    body = {
        "model": provider["model"],
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2048,
    }
    try:
        async with httpx.AsyncClient(timeout=LLM_INFERENCE_TIMEOUT) as client:
            resp = await client.post(
                provider["url"],
                json=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
            )
            raw = resp.json()
    except Exception as exc:
        return {"success": False, "data": None, "error": str(exc), "attempts": 1}
    choices = raw.get("choices", [])
    reply = ""
    if choices:
        reply = choices[0].get("message", {}).get("content", "")
    usage = raw.get("usage", {})
    return {
        "success": True,
        "data": {"data": {"reply": reply, "usage": usage}},
        "attempts": 1,
    }
