# 修复·批次1（P0-1～P0-3：crawler核心修复）

你是 Codex CLI。请直接执行，不要调用其他编码Agent，你自己干。

## 1. P0-1：async_crawl 缺少 Playwright 渲染判断

**文件：** `cloud/app/crawler/engine.py`

在 `async_crawl()` 方法中添加与 `crawl()` 相同的 `config.render_required` 判断。找到 `async_crawl` 方法，看 `crawl()` 中如何判断 `render_required` 并调用 `_render_with_playwright()`，在 `async_crawl` 中做同样的事。

## 2. P0-2：analysis/__init__.py 静默吞异常

**文件：** `cloud/app/crawler/analysis/__init__.py`

找到两处 `except Exception: records = []`：
- 第85行附近：`load_price_records` 函数中
- 第195行附近：`load_opinion_records` 函数中

改为：
```python
except ImportError:
    records = []  # 无第三方库时降级
except (sqlite3.Error, OSError) as e:
    logger.warning("DB error in %s: %s", _name, e)
    records = []
```

导入 `logging`，`logger = logging.getLogger(__name__)`。

## 3. P0-3：storage.py SQL 注入风险

**文件：** `cloud/app/crawler/storage.py` 第104-116行

将 `f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})"` 改为使用带引号的列名：
```python
column_sql = ", ".join(f'"{col}"' for col in columns)
```

确保列名被双引号正确引用。
