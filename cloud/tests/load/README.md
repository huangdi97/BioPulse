# 负载测试

## 用途

使用异步 HTTP 客户端模拟多 Agent 并发请求，采集 p50/p95/p99 延迟、错误率等指标。

## 用法

```bash
# 基本用法（5 并发，10 秒）
python cloud/tests/load/load_test_agent.py --concurrent 5 --duration 10

# 指定目标 URL
python cloud/tests/load/load_test_agent.py --concurrent 10 --duration 30 --url http://localhost:8000/agent/execute

# 限制最大并发数（避免连接池耗尽）
python cloud/tests/load/load_test_agent.py --concurrent 50 --duration 60 --max-concurrent 20
```

## 场景配置

`test_scenarios.json` 定义了 3 个预设场景：

| 场景 | 并发数 | 时长 | 预期 p99 | 预期错误率 |
|------|--------|------|----------|------------|
| light | 10 | 30s | <5s | <1% |
| medium | 30 | 60s | <8s | <5% |
| heavy | 50 | 120s | <15s | <10% |

## 输出格式

```json
{
  "config": {"concurrent": 5, "duration_seconds": 10},
  "results": {
    "total_requests": 42,
    "success_count": 40,
    "error_count": 2,
    "error_rate_pct": 4.76,
    "latency_ms": {"p50": 123.45, "p95": 456.78, "p99": 890.12},
    "token_consumption": 0,
    "actual_duration_seconds": 10.02
  }
}
```