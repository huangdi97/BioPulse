## P0-1：crawler/engine.py async_crawl 缺少 Playwright 渲染判断

文件：cloud/app/crawler/engine.py

问题：crawl() 同步方法有 if config and config.render_required: self._render_with_playwright(...) 的判断，但 async_crawl() 异步方法缺少此判断，始终走 HTTP 请求。

改动：在 async_crawl() 方法中添加与 crawl() 相同的 config.render_required 判断逻辑，需要渲染时调用 _render_with_playwright()。

验收：async_crawl 中应能正确识别 render_required=True 的数据源并走渲染路径。

## P0-2：crawler/analysis/__init__.py 静默吞异常

文件：cloud/app/crawler/analysis/__init__.py

问题：第85行和第195行附近有两处 except Exception: records = [] 裸异常捕获，吞掉了所有错误。

改动：区分异常类型——except ImportError 时降级到规则引擎，except (sqlite3.Error, httpx.RequestError) 时记录日志并返回标记，不允许吞没未预期的异常。

验收：python -c "from cloud.app.crawler.analysis import *; print('ok')" 通过。

## P0-3：crawler/storage.py SQL 注入风险

文件：cloud/app/crawler/storage.py

问题：第104-116行 f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})" 中 column_sql 从模型字段名拼接。

改动：改用 column_sql = ", ".join(f'"{col}"' for col in columns) 确保列名被正确引用。

验收：代码检查无 f-string 拼接列名。
