# 修复·批次6（P2-1～P2-3：集成 + 模板精简 + 模式统一）

你是 Codex CLI。请直接执行，不要调用其他编码Agent，你自己干。

## 1. P2-1：data_platform 单元测试

基于 P0-4 已创建的 data_platform_router，补充单元测试。

**新建：** `cloud/app/data_platform/tests/__init__.py` 和 `test_basic.py`

最少3个测试用例：
1. ETL Pipeline 执行测试（调用 `ETLPipeline.run()`）
2. OLAP 查询服务测试（空数据集返回空结果）
3. BIViewService 聚合查询测试

## 2. P2-2：shared/database.py 基类（精简10x database.py）

**新建：** `shared/database_shared.py`

提供通用 `SQLiteDatabase` 基类：
```python
class SQLiteDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    
    def init_db(self, schema_sql: str) -> None:
        conn = self.get_connection()
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()
```

⚠️ **注意：** 只新建基类文件，不改动现有 database.py 的 import 路径。现有代码保持完全向后兼容。

## 3. P2-3：base.py 模式统一

**文件：** `sales-assistant/app/services/base.py` 和 `cloud/app/services/base.py`

这两个文件目前使用自建的 FastAPI Depends 模式。改为与 `assistant/app/services/base.py`、`opportunity/app/services/base.py`、`sales-coach/app/services/base.py` 一致的 shared.base_service 重导出模式：

```python
from shared.base_service import BaseCrudService as _BaseCrudService
from shared.base_service import BaseService as _BaseService

BaseService = _BaseService
BaseCrudService = _BaseCrudService
```

⚠️ **注意：** 保持所有已有 import 路径 `from X.app.services.base import BaseService` 能正常工作。改动后运行 `python -c "from sales_assistant.app.services.base import BaseService; print('ok')"` 验证。
