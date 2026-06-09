# 修复·批次3（P1-1～P1-3：docstring + 重复代码 + 大文件拆分）

你是 Codex CLI。请直接执行，不要调用其他编码Agent，你自己干。

## 1. P1-1：crawler 模块方法级 docstring

**文件：** `cloud/app/crawler/engine.py`、`storage.py`、`scheduler.py`、`proxy_pool.py`

为以下核心方法补充 docstring（1-3行说明参数和返回值）：

`engine.py`:
- `_fetch_http(url, headers, timeout, proxies, retries)`: 参数、重试逻辑、返回值说明
- `_async_fetch_http(url, headers, timeout, proxies, retries)`: 同上
- `crawl(url, source_type, callback)`: 参数、回调调用时机
- `async_crawl(url, source_type, callback)`: 同上

`storage.py`:
- `save_record(record)`: 返回 auto-increment ID
- `query_records(model, filters)`: 过滤逻辑说明

`scheduler.py`:
- `add_job(source, interval, keywords)`: job_id 生成逻辑
- `remove_job(job_id)`: 删除行为

`proxy_pool.py`:
- `get_proxy()`: 轮换策略说明
- `should_rotate(response)`: 反爬检测阈值

## 2. P1-2：engine.py 抽取公共 HTTP 请求逻辑

**文件：** `cloud/app/crawler/engine.py`

`_fetch_http` 和 `_async_fetch_http` 有约30行重复逻辑（headers构造、超时设置、代理轮换、重试）。

提取公共逻辑为 `_build_request_args(url, source_type, timeout)` 返回 `(headers, proxies)` 元组，在两个方法中调用。

## 3. P1-3：analysis/__init__.py 拆分

**文件：** `cloud/app/crawler/analysis/__init__.py`（237行）

创建 `cloud/app/crawler/analysis/utils.py`，将以下工具函数从 `__init__.py` 移到 `utils.py`：
- `load_price_records`
- `load_opinion_records` 
- `sample_price_records`
- `sample_opinion_records`
- `_stable_score`
- `round_number`

`__init__.py` 改为只做：`from .utils import load_price_records, load_opinion_records, ...`

保留所有 `from .xxx import` 的行不动。
