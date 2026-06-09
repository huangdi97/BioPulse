## P2-4：修复 market-access / clinical-ops / patient-engage 基础测试

已创建测试目录和基础文件，但 conftest.py 有 pytest import path 冲突（多个 conftest 同名导致）。

需要：
1. 删除 market-access/app/tests/conftest.py、clinical-ops/app/tests/conftest.py、patient-engage/app/tests/conftest.py
2. 修改 test_basic.py，让导入路径正确解析（使用 importlib 方式导入各端的 main 模块）

参考其他端可以直接用 importlib.import_module('market-access.app.main') 模式。

验收：venv/bin/python3 -m pytest market-access/app/tests/ clinical-ops/app/tests/ patient-engage/app/tests/ -v 通过。

## P2-5：更新 design.md 第12章差距表

文件：design.md

找到 "增强方向" 部分，更新状态：
- T1 14/14 ✅
- T2 12/12 ✅  
- T3 18/18 ✅
- T4 3/3 ✅

验收：grep "增强方向" design.md 显示实际完成状态。
