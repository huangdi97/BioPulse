"""Agent Runtime LLM class — routing, fallback, and main call orchestration."""

import json
import logging
import time
from datetime import datetime
from functools import partial

from cloud.app.agent_runtime.circuit_breaker import CircuitBreaker
from cloud.app.agent_runtime.metrics import agent_llm_duration, agent_tokens_total
from cloud.app.agent_runtime.retry import async_retry_with_backoff, retry_with_backoff
from cloud.app.agent_runtime.runtime_llm.config import (
    FALLBACK_CHAIN,
    AllModelsFailedError,
    compress_messages,
    estimate_complexity,
    estimate_token_count,
)
from cloud.app.agent_runtime.runtime_llm.request import (
    build_cloud_body,
    call_local,
    call_local_async,
    call_provider,
    call_provider_async,
    raw_llm_call,
    raw_llm_call_async,
)
from cloud.app.agent_runtime.runtime_llm.response import annotate_route_result, usage_from_route_result
from shared.config import settings as config_settings

logger = logging.getLogger(__name__)


class RuntimeLLM:
    """提供 LLM 调用、Token 估算与消息压缩的混入类。"""

    @staticmethod
    def _estimate_token_count(messages: list[dict]) -> int:
        """估算消息列表的 Token 数量。"""
        return estimate_token_count(messages)

    def _compress_messages(self, messages: list[dict]) -> list[dict]:
        """压缩消息列表以降低 Token 消耗。"""
        return compress_messages(messages)

    def _raw_llm_call(self, request_body: dict) -> dict:
        """执行同步原始 LLM 调用。"""
        return raw_llm_call(request_body, self._auth_header)

    async def _raw_llm_call_async(self, request_body: dict) -> dict:
        """执行异步原始 LLM 调用。"""
        return await raw_llm_call_async(request_body, self._auth_header)

    @staticmethod
    def _estimate_complexity(messages: list[dict]) -> int:
        """估算消息列表的复杂度等级。"""
        return estimate_complexity(messages)

    def _call_local(self, messages: list[dict], temperature: float) -> dict:
        """调用本地模型并支持降级到云端。"""
        return call_local(
            config_settings,
            messages,
            temperature,
            fallback_fn=lambda: self._call_cloud_normal(messages, temperature),
        )

    async def _call_local_async(self, messages: list[dict], temperature: float) -> dict:
        """异步调用本地模型并支持降级到云端。"""
        return await call_local_async(
            config_settings,
            messages,
            temperature,
            fallback_fn=lambda: self._call_cloud_normal_async(messages, temperature),
        )

    def _call_cloud_normal(self, messages: list[dict], temperature: float) -> dict:
        """通过云端正常运行模式调用 LLM。"""
        body = build_cloud_body(messages, temperature)
        fn = partial(self._raw_llm_call, body)
        return retry_with_backoff(fn, max_attempts=4, base_delay=1.0)

    async def _call_cloud_normal_async(self, messages: list[dict], temperature: float) -> dict:
        """异步通过云端正常运行模式调用 LLM。"""
        body = build_cloud_body(messages, temperature)
        fn = partial(self._raw_llm_call_async, body)
        return await async_retry_with_backoff(fn, max_attempts=4, base_delay=1.0)

    def _call_cloud_agent(self, messages: list[dict], temperature: float) -> dict:
        """通过云端 Agent 模式调用 LLM。"""
        body = build_cloud_body(messages, temperature, agent_mode=True)
        fn = partial(self._raw_llm_call, body)
        return retry_with_backoff(fn, max_attempts=4, base_delay=1.0)

    async def _call_cloud_agent_async(self, messages: list[dict], temperature: float) -> dict:
        """异步通过云端 Agent 模式调用 LLM。"""
        body = build_cloud_body(messages, temperature, agent_mode=True)
        fn = partial(self._raw_llm_call_async, body)
        return await async_retry_with_backoff(fn, max_attempts=4, base_delay=1.0)

    @staticmethod
    def _usage_from_route_result(result: dict) -> dict:
        """从路由结果中提取用量信息。"""
        return usage_from_route_result(result)

    @staticmethod
    def _annotate_route_result(result: dict, model_tier: str) -> dict:
        """为路由结果添加模型层级标注。"""
        return annotate_route_result(result, model_tier)

    def _route_call(self, messages: list[dict], temperature: float, force_level: int | None = None) -> dict:
        """根据复杂度和配置路由 LLM 调用。"""
        if force_level is not None:
            level = force_level
        elif not config_settings.ai_routing_enabled:
            return self._annotate_route_result(self._call_cloud_normal(messages, temperature), "cloud_normal")
        else:
            level = self._estimate_complexity(messages)

        if level <= 2:
            return self._annotate_route_result(self._call_local(messages, temperature), "local")
        if level == 3:
            return self._annotate_route_result(self._call_cloud_normal(messages, temperature), "cloud_normal")
        return self._annotate_route_result(self._call_cloud_agent(messages, temperature), "cloud_agent")

    async def _route_call_async(self, messages: list[dict], temperature: float, force_level: int | None = None) -> dict:
        """异步路由 LLM 调用。"""
        if force_level is not None:
            level = force_level
        elif not config_settings.ai_routing_enabled:
            return self._annotate_route_result(await self._call_cloud_normal_async(messages, temperature), "cloud_normal")
        else:
            level = self._estimate_complexity(messages)

        if level <= 2:
            return self._annotate_route_result(await self._call_local_async(messages, temperature), "local")
        if level == 3:
            return self._annotate_route_result(await self._call_cloud_normal_async(messages, temperature), "cloud_normal")
        return self._annotate_route_result(await self._call_cloud_agent_async(messages, temperature), "cloud_agent")

    @staticmethod
    def _call_provider(messages: list[dict], temperature: float, provider: dict) -> dict:
        """调用指定供应商的 LLM。"""
        return call_provider(messages, temperature, provider)

    @staticmethod
    async def _call_provider_async(messages: list[dict], temperature: float, provider: dict) -> dict:
        """异步调用指定供应商的 LLM。"""
        return await call_provider_async(messages, temperature, provider)

    def call_llm_with_fallback(self, messages: list[dict], temperature: float, fallback_strategy: str = "fail_fast") -> dict:
        """按供应商链依次调用 LLM，支持降级策略。"""
        errors = []
        for provider in FALLBACK_CHAIN:
            logger.info("Trying provider: %s model: %s", provider["provider"], provider["model"])
            start = time.time()
            result = self._call_provider(messages, temperature, provider)
            elapsed = round(time.time() - start, 3)
            if result["success"]:
                logger.info("Provider %s succeeded in %.3fs", provider["provider"], elapsed)
                return result
            errors.append({"provider": provider["provider"], "model": provider["model"], "error": result.get("error", "unknown"), "elapsed": elapsed})
            logger.warning("Provider %s failed in %.3fs: %s", provider["provider"], elapsed, result.get("error"))
            if fallback_strategy == "fail_fast":
                break
        raise AllModelsFailedError(errors)

    async def call_llm_with_fallback_async(self, messages: list[dict], temperature: float, fallback_strategy: str = "fail_fast") -> dict:
        """异步按供应商链依次调用 LLM，支持降级策略。"""
        errors = []
        for provider in FALLBACK_CHAIN:
            logger.info("Trying provider: %s model: %s", provider["provider"], provider["model"])
            start = time.time()
            result = await self._call_provider_async(messages, temperature, provider)
            elapsed = round(time.time() - start, 3)
            if result["success"]:
                logger.info("Provider %s succeeded in %.3fs", provider["provider"], elapsed)
                return result
            errors.append({"provider": provider["provider"], "model": provider["model"], "error": result.get("error", "unknown"), "elapsed": elapsed})
            logger.warning("Provider %s failed in %.3fs: %s", provider["provider"], elapsed, result.get("error"))
            if fallback_strategy == "fail_fast":
                break
        raise AllModelsFailedError(errors)

    def _call_ai(self, messages: list[dict], temperature: float, step: int = 0, force_level: int | None = None) -> dict:
        """执行同步 AI 调用并收集运行指标。"""
        prompt_text = json.dumps(messages, ensure_ascii=False)
        input_len = len(prompt_text)
        call_start = time.time()

        rate_limiter = getattr(self, "_rate_limiter", None)
        if rate_limiter is not None:
            agent_key = getattr(self, "_trace_id", "unknown")
            rate_limiter.check_or_raise(f"agent_llm:{agent_key}")

        circuit_breaker: CircuitBreaker | None = getattr(self, "_circuit_breaker", None)
        if circuit_breaker is not None:
            result = circuit_breaker.call(self._route_call, messages, temperature, force_level)
        else:
            result = self._route_call(messages, temperature, force_level)

        duration_s = round(time.time() - call_start, 3)

        if result["success"]:
            ai_response = result["data"]
            data = ai_response.get("data", {})
            raw_response = json.dumps(ai_response, ensure_ascii=False)
            output_len = len(raw_response)

            tracer = getattr(self, "_tracer", None)
            if tracer:
                tier = result.get("model_tier", "cloud_normal")
                usage = data.get("usage", {})
                tracer.log_llm_call(
                    tier,
                    int(usage.get("prompt_tokens", 0) or 0),
                    int(usage.get("completion_tokens", 0) or 0),
                    int(duration_s * 1000),
                )

            self._trace_data.append(
                {
                    "step": step,
                    "input_len": input_len,
                    "output_len": output_len,
                    "duration_s": duration_s,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            model_tier = result.get("model_tier", "cloud_normal")
            agent_llm_duration.labels(agent_name=getattr(self, "_trace_id", "unknown"), model=model_tier).observe(duration_s)
            usage = data.get("usage", {})
            total_tokens = int(usage.get("total_tokens", 0) or 0)
            if total_tokens:
                agent_tokens_total.labels(agent_name=getattr(self, "_trace_id", "unknown")).inc(total_tokens)
            return {
                "reply": data.get("reply", ""),
                "usage": usage,
                "prompt": prompt_text,
                "raw_response": raw_response,
                "retry_count": result["attempts"] - 1,
                "cost": result.get("cost", {}),
                "model_tier": model_tier,
            }
        raise RuntimeError(f"LLM call failed after {result['attempts']} attempts: {result['error']}")

    async def _call_ai_async(self, messages: list[dict], temperature: float, step: int = 0, force_level: int | None = None) -> dict:
        """执行异步 AI 调用并收集运行指标。"""
        prompt_text = json.dumps(messages, ensure_ascii=False)
        input_len = len(prompt_text)
        call_start = time.time()

        rate_limiter = getattr(self, "_rate_limiter", None)
        if rate_limiter is not None:
            agent_key = getattr(self, "_trace_id", "unknown")
            rate_limiter.check_or_raise(f"agent_llm:{agent_key}")

        circuit_breaker: CircuitBreaker | None = getattr(self, "_circuit_breaker", None)
        if circuit_breaker is not None:
            result = circuit_breaker.call(self._route_call_async, messages, temperature, force_level)
        else:
            result = await self._route_call_async(messages, temperature, force_level)

        duration_s = round(time.time() - call_start, 3)

        if result["success"]:
            ai_response = result["data"]
            data = ai_response.get("data", {})
            raw_response = json.dumps(ai_response, ensure_ascii=False)
            output_len = len(raw_response)

            tracer = getattr(self, "_tracer", None)
            if tracer:
                tier = result.get("model_tier", "cloud_normal")
                usage = data.get("usage", {})
                tracer.log_llm_call(
                    tier,
                    int(usage.get("prompt_tokens", 0) or 0),
                    int(usage.get("completion_tokens", 0) or 0),
                    int(duration_s * 1000),
                )

            self._trace_data.append(
                {
                    "step": step,
                    "input_len": input_len,
                    "output_len": output_len,
                    "duration_s": duration_s,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            model_tier = result.get("model_tier", "cloud_normal")
            agent_llm_duration.labels(agent_name=getattr(self, "_trace_id", "unknown"), model=model_tier).observe(duration_s)
            usage = data.get("usage", {})
            total_tokens = int(usage.get("total_tokens", 0) or 0)
            if total_tokens:
                agent_tokens_total.labels(agent_name=getattr(self, "_trace_id", "unknown")).inc(total_tokens)
            return {
                "reply": data.get("reply", ""),
                "usage": usage,
                "prompt": prompt_text,
                "raw_response": raw_response,
                "retry_count": result["attempts"] - 1,
                "cost": result.get("cost", {}),
                "model_tier": model_tier,
            }
        raise RuntimeError(f"LLM call failed after {result['attempts']} attempts: {result['error']}")
