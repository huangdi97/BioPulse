## P2-4：补充 market-access / clinical-ops / patient-engage 单元测试

为每个端添加最少2个基础测试：
- API 可达性测试（health endpoint）
- 各新增 router 的基本 HTTP smoke test

文件：
market-access/app/tests/__init__.py
market-access/app/tests/test_basic.py
clinical-ops/app/tests/__init__.py
clinical-ops/app/tests/test_basic.py
patient-engage/app/tests/__init__.py
patient-engage/app/tests/test_basic.py

验收：pytest market-access/app/tests/ clinical-ops/app/tests/ patient-engage/app/tests/ -v 通过。

## P2-5：更新 design.md 第12章差距表

文件：design.md

问题：第12章差距表显示 "增强方向 T1-T4 | 36项 | 0/36 未开始 🔴"，但实际代码已实现。

改动：更新差距表：
- Agent覆盖率：更新为当前实际状态
- 增强方向：T1 14/14 ✅，T2 12/12 ✅，T3 18/18 ✅，T4 3/3 ✅
- 飞检仪表盘、HCP评分、MDM 标注实际实现状态

验收：grep "增强方向" design.md | head -5 显示实际完成比例。

## P2-6：models.py date_type 别名清理

文件：cloud/app/crawler/models.py 第5行

问题：from datetime import date as date_type — 冗余别名。

改动：移除 date_type 别名，直接使用 date。

验收：文件中无 date_type 引用。
