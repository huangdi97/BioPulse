## P1-4：comparison_analyzer.py 空记录逻辑缺陷

文件：cloud/app/crawler/analysis/comparison_analyzer.py 第48行

问题：latest_date = max((record["date"] for record in records), default="") — 当 records 为空时 latest_date=""，后续 record["date"] == "" 会错误匹配所有空字符串日期的记录。

改动：records 为空时直接返回空结果或 None，不做空字符串匹配。

验收：空记录输入不产生错误匹配。

## P1-5：proxy_pool.py should_rotate 副作用

文件：cloud/app/crawler/proxy_pool.py 第78行

问题：should_rotate 中 response.text[:2000] 消耗了响应体，可能导致后续代码无法再次读取。

改动：改为检查 response.content（bytes，不会消耗）或使用 response 的 headers 做反爬检测。

验收：should_rotate 调用后响应体仍可读取。

## P1-6：scheduler.py Timer 递归重叠风险

文件：cloud/app/crawler/scheduler.py 第199-204行

问题：APScheduler fallback 模式使用 threading.Timer 链式调用，如果任务执行时间超过 interval，会出现多个 runner 重叠。

改动：在 fallback 模式中增加锁或检查上次执行是否已完成再启动下一次。

验收：scheduler.py fallback 模式能正确处理执行超时。
