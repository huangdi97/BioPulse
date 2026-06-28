"""Agent 负载测试脚本 — 模拟并发 Agent 调用。"""

import argparse
import asyncio
import statistics
import time

import aiohttp

BASE_URL = "http://localhost:8000"


async def run_single_agent(session: aiohttp.ClientSession, agent_key: str, goal: str, idx: int) -> dict:
    start = time.time()
    try:
        async with session.post(
            f"{BASE_URL}/agent/runtime/execute",
            json={"agent_key": agent_key, "goal": goal},
            timeout=aiohttp.ClientTimeout(total=60),
        ) as resp:
            latency = (time.time() - start) * 1000
            status = resp.status
            await resp.json()
            return {"idx": idx, "success": 200 <= status < 300, "status": status, "latency_ms": round(latency, 2), "error": ""}
    except Exception as e:
        latency = (time.time() - start) * 1000
        return {"idx": idx, "success": False, "status": 0, "latency_ms": round(latency, 2), "error": str(e)}


async def worker(
    session: aiohttp.ClientSession,
    queue: asyncio.Queue,
    results: list,
):
    while True:
        try:
            idx, agent_key, goal = queue.get_nowait()
        except asyncio.QueueEmpty:
            return
        result = await run_single_agent(session, agent_key, goal, idx)
        results.append(result)
        queue.task_done()


async def run_load_test(concurrency: int, duration: int, agent_key: str, goal: str):
    queue = asyncio.Queue()
    idx = 0
    start_time = time.time()
    while time.time() - start_time < duration:
        await queue.put((idx, agent_key, goal))
        idx += 1

    results: list[dict] = []
    connector = aiohttp.TCPConnector(limit=concurrency, force_close=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [asyncio.create_task(worker(session, queue, results)) for _ in range(concurrency)]
        await asyncio.gather(*tasks)

    return results


def print_report(results: list[dict], duration: int):
    total = len(results)
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    latencies = [r["latency_ms"] for r in results]

    if not latencies:
        print("No results collected.")
        return

    sorted_lat = sorted(latencies)
    p50 = statistics.median(sorted_lat)
    p95 = sorted_lat[int(len(sorted_lat) * 0.95)]
    p99 = sorted_lat[int(len(sorted_lat) * 0.99)]
    avg_lat = statistics.mean(latencies)
    qps = total / duration

    print(f"\n{'=' * 50}")
    print(f"Load Test Report ({duration}s)")
    print(f"{'=' * 50}")
    print(f"  Total requests:  {total}")
    print(f"  Successful:      {len(successes)} ({len(successes) / total * 100:.1f}%)")
    print(f"  Failed:          {len(failures)} ({len(failures) / total * 100:.1f}%)")
    print(f"  QPS:             {qps:.1f}")
    print(f"  Avg latency:     {avg_lat:.1f}ms")
    print(f"  P50 latency:     {p50:.1f}ms")
    print(f"  P95 latency:     {p95:.1f}ms")
    print(f"  P99 latency:     {p99:.1f}ms")
    print(f"{'=' * 50}\n")


def main():
    parser = argparse.ArgumentParser(description="Agent Load Test")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent requests")
    parser.add_argument("--duration", type=int, default=30, help="Test duration in seconds")
    parser.add_argument("--agent-key", type=str, default="default", help="Agent key to test")
    parser.add_argument("--goal", type=str, default="Hello, please respond briefly.", help="Agent goal")
    parser.add_argument("--url", type=str, default=BASE_URL, help="Base URL")
    args = parser.parse_args()

    global BASE_URL
    BASE_URL = args.url

    print(f"Starting load test: concurrency={args.concurrency}, duration={args.duration}s, agent={args.agent_key}")
    results = asyncio.run(run_load_test(args.concurrency, args.duration, args.agent_key, args.goal))
    print_report(results, args.duration)


if __name__ == "__main__":
    main()
