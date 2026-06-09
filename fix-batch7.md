# 修复·批次7（P2-4～P2-6：测试 + design.md + 别名清理）

你是 Codex CLI。请直接执行，不要调用其他编码Agent，你自己干。

## 1. P2-4：3端补充单元测试

**新建目录和文件：**

1. `market-access/app/tests/__init__.py`、`market-access/app/tests/test_basic.py`
2. `clinical-ops/app/tests/__init__.py`、`clinical-ops/app/tests/test_basic.py`
3. `patient-engage/app/tests/__init__.py`、`patient-engage/app/tests/test_basic.py`

每个 test_basic.py 最少2个测试：
1. API health endpoint 可达性测试
2. 各端新增 router 的基本 HTTP smoke test（如 `/api/price/province`、`/api/milestone/gantt`、`/api/patient/compliance`）

使用 FastAPI TestClient。

## 2. P2-5：更新 design.md 第12章差距表

**文件：** `design.md`

找到第十二章（搜索`# 设计与代码的差距`或`第12章`），更新差距表数据：
- Agent覆盖率不动（维持原状）
- 增强方向 T1-T4：改为 `36/36 ✅ 已完成`
- 补充说明各批次对应的实现批次
- 三个恢复端状态：已增强

## 3. P2-6：models.py date_type 别名清理

**文件：** `cloud/app/crawler/models.py` 第5行

`from datetime import date as date_type` → 移除 `as date_type` 别名

将文件中所有 `date_type` 引用改为 `date`。

确认：`grep -n "date_type" cloud/app/crawler/models.py` 应无输出。
