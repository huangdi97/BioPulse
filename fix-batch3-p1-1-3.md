## P1-1：crawler 模块方法级 docstring 补充

文件：cloud/app/crawler/ 下所有 *.py 文件

问题：模块级 docstring 100% 覆盖，类级 OK，但方法级覆盖率仅 ~22%。核心方法如 engine.py 的 _fetch_http、_async_fetch_http、crawl、async_crawl，storage.py 的 save_record、query_records 等均无 docstring。

改动：为所有公开方法补充 docstring（说明参数、返回值、异常），私有关键方法至少加 # 注释。每个方法 1-3 行。

验收：核心方法均有 docstring。

## P1-2：engine.py 提取 _fetch_http 和 _async_fetch_http 公共逻辑

文件：cloud/app/crawler/engine.py

问题：_fetch_http（~30行）和 _async_fetch_http（~30行）逻辑几乎完全相同，仅同步/异步调用不同。

改动：提取公共 HTTP 请求逻辑（headers构造、超时设置、代理轮换、重试）为纯函数或私有方法，同步/异步只在外层包装 await/result。

验收：公共逻辑不在两个方法中重复。

## P1-3：analysis/__init__.py 拆分 — 237行Mega文件

文件：cloud/app/crawler/analysis/__init__.py（237行）

问题：既做包导出又包含 11 个工具函数，混合职责。

改动：将工具函数（load_price_records、load_opinion_records、sample_price_records、_stable_score、round_number 等）抽到 analysis/utils.py，__init__.py 只做 from .utils import ... 导出。

验收：__init__.py 不超过 50 行（仅导出），工具函数在 utils.py 中。
