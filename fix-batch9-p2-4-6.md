## P2-4：补充 market-access / clinical-ops / patient-engage 单元测试

为每个端添加基础测试。

创建文件：
market-access/app/tests/__init__.py（空文件）
market-access/app/tests/test_basic.py
clinical-ops/app/tests/__init__.py（空文件）
clinical-ops/app/tests/test_basic.py
patient-engage/app/tests/__init__.py（空文件）
patient-engage/app/tests/test_basic.py

每个 test_basic.py 内容参考 cloud/app/tests/test_cloud.py 的模式，至少包含2个测试：
- 测试导入正常
- 简单功能测试

验收：python -m pytest market-access/app/tests/ clinical-ops/app/tests/ patient-engage/app/tests/ -v 通过。

## P2-5：更新 design.md 第12章差距表

文件：design.md

找到第12章"差距分析"部分，更新以下内容：
- 增强方向：T1 14/14 ✅，T2 12/12 ✅，T3 18/18 ✅，T4 3/3 ✅
- 飞检仪表盘、HCP评分、MDM 标注实际实现状态为已实现

用 grep "增强方向" design.md 确认修改完成。

## P2-6：models.py date_type 别名清理

文件：cloud/app/crawler/models.py

把 from datetime import date as date_type 改为 from datetime import date，文件中所有 date_type 引用改为 date。

验收：grep "date_type" cloud/app/crawler/models.py 无匹配。
