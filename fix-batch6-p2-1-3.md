## P2-1：数据中台完整集成（补充P0-4）

文件：cloud/app/data_platform/

补充：在 P0-4 创建 router 的基础上，为 data_platform 添加单元测试，覆盖 ETL、OLAP、BI 三层核心逻辑。最少 3 个测试用例。

验收：python -m pytest cloud/app/data_platform/tests/ -v 通过。

## P2-2：10x database.py 重复模板精简

文件：各端 */app/database.py（10个文件）

改动：
1. 在 shared/ 中创建 shared/database.py 提供通用 SQLiteDatabase 基类
2. 各端 database.py 继承基类，只保留本端特有的表定义
3. 保持向后兼容（不修改 import 路径）

注意：此改动影响面大，注意不要破坏现有启动流程。

验收：各端启动正常，ls -la */app/database.py 仍在。

## P2-3：base.py 模式统一

文件：cloud/app/services/base.py 和 sales-assistant/app/services/base.py

问题：3端用 shared.base_service 重导出模式，2端用自建 FastAPI Depends 模式。

改动：统一到 shared.base_service 模式。修改 sales-assistant 和 cloud 的 base.py 为与另外3端一致的重导出方式。

验收：所有端的 from X.app.services.base import BaseService 都能正常工作。
