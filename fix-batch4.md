# 修复·批次4（P1-4～P1-6：逻辑缺陷 + 响应体副作用 + Timer重叠）

你是 Codex CLI。请直接执行，不要调用其他编码Agent，你自己干。

## 1. P1-4：comparison_analyzer.py 空记录逻辑缺陷

**文件：** `cloud/app/crawler/analysis/comparison_analyzer.py` 第48行

当前：`latest_date = max((record["date"] for record in records), default="")`

改为：
```python
if not records:
    return {"product_id": product_id, "note": "no data", "competitors": []}
latest_date = max(record["date"] for record in records)
```

确保函数在空记录时提前返回而不继续执行后续逻辑。

## 2. P1-5：proxy_pool.py should_rotate 响应体副作用

**文件：** `cloud/app/crawler/proxy_pool.py` 第78行

当前：`response.text[:2000]` 消耗了响应体。

改为使用 `response.content`（bytes 流可重复读取）或只检查响应头中的反爬标记：
```python
content_sample = response.content[:2000]
# 检查 403/429 状态码或反爬标记
```

## 3. P1-6：scheduler.py Timer 递归重叠

**文件：** `cloud/app/crawler/scheduler.py` 第199-204行

在 APScheduler 不可用的 fallback 模式中，添加执行锁防止 Timer 重叠：

```python
import threading
_job_locks: dict[str, threading.Lock] = {}
```

在 Timer 回调开始时获取锁，结束时释放。如果锁已被占有则跳过本次执行。
