#!/usr/bin/env python3
"""性能测试：模拟并发 Agent 请求，输出延迟统计。"""

import argparse
import asyncio
import json
import random
import time


async def mock_agent_request(delay: float) -> float:
    """模拟一次 Agent 请求，返回耗时（秒）。"""
    start = time.monotonic()
    # 模拟 LLM 调用和工具执行的延迟
    await asyncio.sleep(delay)
    return time.monotonic() - start


async def run_concurrent(count: int, duration: int) -> dict:
    """模拟 count 个并发请求，持续 duration 秒。"""
    latencies = []
    errors = 0
    end_time = time.monotonic() + duration
    tasks = []

    async def worker():
        nonlocal errors
        while time.monotonic() < end_time:
            delay = random.uniform(0.1, 0.5)
            try:
                lat = await mock_agent_request(delay)
                latencies.append(lat)
            except Exception:
                errors += 1
            await asyncio.sleep(random.uniform(0.05, 0.2))

    tasks = [asyncio.create_task(worker()) for _ in range(count)]
    await asyncio.gather(*tasks)

    latencies.sort()
    total = len(latencies)

    def percentile(p):
        idx = int(total * p / 100)
        return round(latencies[min(idx, total - 1)] * 1000, 2) if total > 0 else 0

    return {
        "concurrent": count,
        "duration_seconds": duration,
        "total_requests": total,
        "errors": errors,
        "error_rate": round(errors / max(total, 1), 4),
        "latency_ms": {
            "p50": percentile(50),
            "p95": percentile(95),
            "p99": percentile(99),
            "min": round(latencies[0] * 1000, 2) if total > 0 else 0,
            "max": round(latencies[-1] * 1000, 2) if total > 0 else 0,
            "avg": round(sum(latencies) / max(total, 1) * 1000, 2) if total > 0 else 0,
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BioPulse 性能测试")
    parser.add_argument("--concurrent", type=int, default=5, help="并发数")
    parser.add_argument("--duration", type=int, default=10, help="测试持续时间（秒）")
    args = parser.parse_args()

    result = asyncio.run(run_concurrent(args.concurrent, args.duration))
    print(json.dumps(result, indent=2, ensure_ascii=False))
