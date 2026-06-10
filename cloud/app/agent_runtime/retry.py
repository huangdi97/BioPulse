"""指数退避重试模块，支持 HTTP 错误重试及 429 限流处理。"""

import asyncio
import logging
import random
import time
from urllib.error import HTTPError, URLError

import httpx

logger = logging.getLogger(__name__)


def retry_with_backoff(
    fn,
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    retryable_exceptions=None,
):
    if retryable_exceptions is None:
        retryable_exceptions = (HTTPError, URLError, TimeoutError, httpx.TimeoutException, httpx.HTTPError)

    total_delay = 0.0
    last_error = ""

    for attempt in range(max_attempts):
        try:
            data = fn()
            return {
                "success": True,
                "data": data,
                "attempts": attempt + 1,
                "total_delay_ms": int(total_delay * 1000),
                "error": None,
            }
        except retryable_exceptions as e:
            last_error = str(e)
            if attempt == max_attempts - 1:
                break

            delay = base_delay * (2**attempt)
            if isinstance(e, HTTPError) and e.code == 429:
                retry_after = e.headers.get("Retry-After")
                if retry_after:
                    try:
                        delay = float(retry_after)
                    except ValueError:
                        logger.warning("Failed to parse Retry-After header '%s'", retry_after, exc_info=True)

            delay = min(delay, max_delay)
            jitter = random.uniform(-0.2, 0.2)
            delay *= 1.0 + jitter

            time.sleep(delay)
            total_delay += delay
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "attempts": attempt + 1,
                "total_delay_ms": int(total_delay * 1000),
                "error": str(e),
            }

    return {
        "success": False,
        "data": None,
        "attempts": max_attempts,
        "total_delay_ms": int(total_delay * 1000),
        "error": last_error,
    }


async def async_retry_with_backoff(
    fn,
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    retryable_exceptions=None,
):
    if retryable_exceptions is None:
        retryable_exceptions = (HTTPError, URLError, TimeoutError, httpx.TimeoutException, httpx.HTTPError)

    total_delay = 0.0
    last_error = ""
    for attempt in range(max_attempts):
        try:
            data = await fn()
            return {
                "success": True,
                "data": data,
                "attempts": attempt + 1,
                "total_delay_ms": int(total_delay * 1000),
                "error": None,
            }
        except retryable_exceptions as e:
            last_error = str(e)
            if attempt == max_attempts - 1:
                break

            delay = base_delay * (2**attempt)
            if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 429:
                retry_after = e.response.headers.get("Retry-After")
                if retry_after:
                    try:
                        delay = float(retry_after)
                    except ValueError:
                        logger.warning("Failed to parse Retry-After header '%s'", retry_after, exc_info=True)

            delay = min(delay, max_delay)
            jitter = random.uniform(-0.2, 0.2)
            delay *= 1.0 + jitter

            await asyncio.sleep(delay)
            total_delay += delay
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "attempts": attempt + 1,
                "total_delay_ms": int(total_delay * 1000),
                "error": str(e),
            }

    return {
        "success": False,
        "data": None,
        "attempts": max_attempts,
        "total_delay_ms": int(total_delay * 1000),
        "error": last_error,
    }
