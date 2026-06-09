## 修复 pytest namespace 冲突

多个子项目（clinical-ops、patient-engage、market-access）都有 `app/tests/` 目录，pytest 收集测试时 `app.tests` module 缓存冲突，导致 clinical-ops 和 patient-engage 的测试无法加载。

修复方案：
1. 删除 clinical-ops/app/tests/__init__.py
2. 删除 patient-engage/app/tests/__init__.py
3. 删除 market-access/app/tests/__init__.py

去掉 __init__.py 后这些目录变为隐式命名空间包（PEP 420），pytest 可以独立收集每个子项目的测试。

验收：
venv/bin/python3 -m pytest market-access/app/tests/ clinical-ops/app/tests/ patient-engage/app/tests/ -v
全部通过无 ERROR。
