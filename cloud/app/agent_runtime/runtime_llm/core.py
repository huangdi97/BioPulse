"""Agent Runtime LLM class — routing, fallback, and main call orchestration."""

import logging
import time
from functools import partial

from cloud.app.agent_runtime.circuit_breaker import CircuitBreaker
from cloud.app.agent_runtime.retry import async_retry_with_backoff, retry_with_backoff
from cloud.app.agent_runtime.runtime_llm.call_orchestration import process_ai_response
from cloud.app.agent_runtime.runtime_llm.config import (
    AllModelsFailedError,
    compress_messages,
    estimate_complexity,
    estimate_token_count,
    get_fallback_chain,
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

    def _do_call_local(self, messages: list[dict], temperature: float, is_async: bool):
        fn = call_local_async if is_async else call_local
        fallback_fn = (
            (lambda: self._call_cloud_normal_async(messages, temperature)) if is_async else (lambda: self._call_cloud_normal(messages, temperature))
        )
        return fn(config_settings, messages, temperature, fallback_fn=fallback_fn)

    def _call_local(self, messages: list[dict], temperature: float) -> dict:
        return self._do_call_local(messages, temperature, False)

    async def _call_local_async(self, messages: list[dict], temperature: float) -> dict:
        return await self._do_call_local(messages, temperature, True)

    def _do_call_cloud(self, messages: list[dict], temperature: float, is_async: bool, agent_mode: bool = False):
        body = build_cloud_body(messages, temperature, agent_mode=agent_mode)
        if is_async:
            fn = partial(self._raw_llm_call_async, body)
            return async_retry_with_backoff(fn, max_attempts=4, base_delay=1.0)
        else:
            fn = partial(self._raw_llm_call, body)
            return retry_with_backoff(fn, max_attempts=4, base_delay=1.0)

    def _call_cloud_normal(self, messages: list[dict], temperature: float) -> dict:
        return self._do_call_cloud(messages, temperature, False)

    async def _call_cloud_normal_async(self, messages: list[dict], temperature: float) -> dict:
        return await self._do_call_cloud(messages, temperature, True)

    def _call_cloud_agent(self, messages: list[dict], temperature: float) -> dict:
        return self._do_call_cloud(messages, temperature, False, agent_mode=True)

    async def _call_cloud_agent_async(self, messages: list[dict], temperature: float) -> dict:
        return await self._do_call_cloud(messages, temperature, True, agent_mode=True)

    @staticmethod
    def _usage_from_route_result(result: dict) -> dict:
        """从路由结果中提取用量信息。"""
        return usage_from_route_result(result)

    @staticmethod
    def _annotate_route_result(result: dict, model_tier: str) -> dict:
        """为路由结果添加模型层级标注。"""
        return annotate_route_result(result, model_tier)

    def _do_route(self, messages: list[dict], temperature: float, force_level: int | None, is_async: bool):
        def _sync():
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

        async def _async():
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

        return _async() if is_async else _sync()

    def _route_call(self, messages: list[dict], temperature: float, force_level: int | None = None) -> dict:
        return self._do_route(messages, temperature, force_level, False)

    async def _route_call_async(self, messages: list[dict], temperature: float, force_level: int | None = None) -> dict:
        return await self._do_route(messages, temperature, force_level, True)

    @staticmethod
    def _call_provider(messages: list[dict], temperature: float, provider: dict) -> dict:
        """调用指定供应商的 LLM。"""
        return call_provider(messages, temperature, provider)

    @staticmethod
    async def _call_provider_async(messages: list[dict], temperature: float, provider: dict) -> dict:
        """异步调用指定供应商的 LLM。"""
        return await call_provider_async(messages, temperature, provider)

    def _do_fallback(self, messages: list[dict], temperature: float, fallback_strategy: str, is_async: bool):
        def _sync():
            errors = []
            for provider in get_fallback_chain():
                logger.info("Trying provider: %s model: %s", provider["provider"], provider["model"])
                start = time.time()
                result = self._call_provider(messages, temperature, provider)
                elapsed = round(time.time() - start, 3)
                if result["success"]:
                    logger.info("Provider %s succeeded in %.3fs", provider["provider"], elapsed)
                    return result
                errors.append(
                    {"provider": provider["provider"], "model": provider["model"], "error": result.get("error", "unknown"), "elapsed": elapsed}
                )
                logger.warning("Provider %s failed in %.3fs: %s", provider["provider"], elapsed, result.get("error"))
                if fallback_strategy == "fail_fast":
                    break
            raise AllModelsFailedError(errors)

        async def _async():
            errors = []
            for provider in get_fallback_chain():
                logger.info("Trying provider: %s model: %s", provider["provider"], provider["model"])
                start = time.time()
                result = await self._call_provider_async(messages, temperature, provider)
                elapsed = round(time.time() - start, 3)
                if result["success"]:
                    logger.info("Provider %s succeeded in %.3fs", provider["provider"], elapsed)
                    return result
                errors.append(
                    {"provider": provider["provider"], "model": provider["model"], "error": result.get("error", "unknown"), "elapsed": elapsed}
                )
                logger.warning("Provider %s failed in %.3fs: %s", provider["provider"], elapsed, result.get("error"))
                if fallback_strategy == "fail_fast":
                    break
            raise AllModelsFailedError(errors)

        return _async() if is_async else _sync()

    def call_llm_with_fallback(self, messages: list[dict], temperature: float, fallback_strategy: str = "fail_fast") -> dict:
        """call llm with fallback."""
        return self._do_fallback(messages, temperature, fallback_strategy, False)

    async def call_llm_with_fallback_async(self, messages: list[dict], temperature: float, fallback_strategy: str = "fail_fast") -> dict:
        """call llm with fallback async."""
        return await self._do_fallback(messages, temperature, fallback_strategy, True)

    def _do_call_ai(self, messages: list[dict], temperature: float, step: int = 0, force_level: int | None = None, is_async: bool = False) -> dict:
        """执行 AI 调用并收集运行指标。"""
        rate_limiter = getattr(self, "_rate_limiter", None)
        if rate_limiter is not None:
            agent_key = getattr(self, "_trace_id", "unknown")
            rate_limiter.check_or_raise(f"agent_llm:{agent_key}")

        def _sync():
            call_start = time.time()
            circuit_breaker: CircuitBreaker | None = getattr(self, "_circuit_breaker", None)
            if circuit_breaker is not None:
                result = circuit_breaker.call(self._route_call, messages, temperature, force_level)
            else:
                result = self._route_call(messages, temperature, force_level)
            duration_s = round(time.time() - call_start, 3)
            tracer = getattr(self, "_tracer", None)
            return process_ai_response(
                result=result,
                messages=messages,
                step=step,
                duration_s=duration_s,
                tracer=tracer,
                trace_id=getattr(self, "_trace_id", "unknown"),
                trace_data=getattr(self, "_trace_data", []),
            )

        async def _async():
            call_start = time.time()
            circuit_breaker: CircuitBreaker | None = getattr(self, "_circuit_breaker", None)
            if circuit_breaker is not None:
                result = circuit_breaker.call(self._route_call_async, messages, temperature, force_level)
            else:
                result = await self._route_call_async(messages, temperature, force_level)
            duration_s = round(time.time() - call_start, 3)
            tracer = getattr(self, "_tracer", None)
            return process_ai_response(
                result=result,
                messages=messages,
                step=step,
                duration_s=duration_s,
                tracer=tracer,
                trace_id=getattr(self, "_trace_id", "unknown"),
                trace_data=getattr(self, "_trace_data", []),
            )

        return _async() if is_async else _sync()

    def _call_ai(self, messages: list[dict], temperature: float, step: int = 0, force_level: int | None = None) -> dict:
        return self._do_call_ai(messages, temperature, step, force_level, False)

    async def _call_ai_async(self, messages: list[dict], temperature: float, step: int = 0, force_level: int | None = None) -> dict:
        return await self._do_call_ai(messages, temperature, step, force_level, True)
