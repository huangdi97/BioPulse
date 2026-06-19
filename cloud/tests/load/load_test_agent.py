"""Agent 负载测试 — 异步并发模拟，记录 p50/p95/p99 延迟与错误率。"""

import argparse
import asyncio
import json
import statistics
import time
from dataclasses import dataclass, field, asdict


@dataclass
class Report:
    total_requests: int = 0
    success_count: int = 0
    error_count: int = 0
    latencies_ms: list[float] = field(default_factory=list)
    token_consumption: int = 0
    duration_seconds: float = 0.0

    @property
    def p50(self) -> float:
        return statistics.median(self.latencies_ms) if self.latencies_ms else 0.0

    @property
    def p95(self) -> float:
        if not self.latencies_ms:
            return 0.0
        sorted_lats = sorted(self.latencies_ms)
        idx = int(len(sorted_lats) * 0.95)
        return sorted_lats[idx]

    @property
    def p99(self) -> float:
        if not self.latencies_ms:
            return 0.0
        sorted_lats = sorted(self.latencies_ms)
        idx = int(len(sorted_lats) * 0.99)
        return sorted_lats[idx]

    @property
    def error_rate(self) -> float:
        return self.error_count / max(self.total_requests, 1) * 100.0


async def _worker(
    worker_id: int,
    url: str,
    duration_seconds: int,
    report: Report,
    semaphore: asyncio.Semaphore,
):
    import httpx

    deadline = time.monotonic() + duration_seconds
    async with httpx.AsyncClient(timeout=10.0) as client:
        while time.monotonic() < deadline:
            async with semaphore:
                start = time.monotonic()
                try:
                    resp = await client.post(
                        url,
                        json={"worker_id": worker_id, "ts": time.time()},
                    )
                    elapsed = (time.monotonic() - start) * 1000
                    report.latencies_ms.append(elapsed)
                    report.total_requests += 1
                    if resp.status_code < 500:
                        report.success_count += 1
                    else:
                        report.error_count += 1
                except Exception:
                    elapsed = (time.monotonic() - start) * 1000
                    report.latencies_ms.append(elapsed)
                    report.total_requests += 1
                    report.error_count += 1


def simulate_concurrent_agents(
    count: int,
    duration_seconds: int,
    url: str = "http://localhost:8000/agent/execute",
    max_concurrent: int = 0,
) -> Report:
    if max_concurrent <= 0:
        max_concurrent = count
    report = Report()
    semaphore = asyncio.Semaphore(max_concurrent)
    async def _run_all():
        tasks = [
            asyncio.create_task(_worker(i, url, duration_seconds, report, semaphore))
            for i in range(count)
        ]
        await asyncio.gather(*tasks)
    start = time.monotonic()
    asyncio.run(_run_all())
    report.duration_seconds = time.monotonic() - start
    return report


def main():
    parser = argparse.ArgumentParser(description="Agent Load Test")
    parser.add_argument("--concurrent", type=int, default=5, help="Number of concurrent agents")
    parser.add_argument("--duration", type=int, default=10, help="Test duration in seconds")
    parser.add_argument("--url", type=str, default="http://localhost:8000/agent/execute")
    parser.add_argument("--max-concurrent", type=int, default=0, help="Max concurrent requests (default: same as --concurrent)")
    args = parser.parse_args()

    report = simulate_concurrent_agents(
        count=args.concurrent,
        duration_seconds=args.duration,
        url=args.url,
        max_concurrent=args.max_concurrent,
    )

    output = {
        "config": {"concurrent": args.concurrent, "duration_seconds": args.duration},
        "results": {
            "total_requests": report.total_requests,
            "success_count": report.success_count,
            "error_count": report.error_count,
            "error_rate_pct": round(report.error_rate, 2),
            "latency_ms": {
                "p50": round(report.p50, 2),
                "p95": round(report.p95, 2),
                "p99": round(report.p99, 2),
            },
            "token_consumption": report.token_consumption,
            "actual_duration_seconds": round(report.duration_seconds, 2),
        },
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()