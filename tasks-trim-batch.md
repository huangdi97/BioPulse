# 批量压缩14个文件到 ≤300 行

## 编码准则（必须遵守）

1. Think Before Coding — 先理解再动手
2. Simplicity First — 用最简单的方式实现
3. Surgical Changes — 精准修改，不碰不相干代码
4. Goal-Driven Execution — 目标：14文件压到 ≤300 行，语法正确可运行
5. 架构优先，拒绝补丁 — 不改变架构
6. 面向组件构建 — 不适用
7. 显式优于隐式 — 保持代码可读性
8. 代码整洁，自文档化 — 保留必要注释
9. 单一职责 — 不改变
10. 组合优于委托 — 不适用
11. 单一状态源 — 不适用
12. 避免语法糖 — 保持原样
13. 命名一致性 — 不改变量名
14. 文件不超过300行 — 本次目标
15. 低耦合 — 不改变
16. 必须用 opencode 写代码 — 本任务由 opencode 执行
17. 启动规则 — 已完成写入
18. 完整准则写入每个 tasks.md — ✅

## 待压缩文件列表

处理以下文件，逐个压缩到 ≤300 行。每次修改前先读取文件内容了解结构。

1. cloud/app/compliance_v2_router.py (586行)
2. cloud/app/services/brain_memory_service.py (446行)
3. cloud/app/services/compliance_enforcer.py (410行)
4. cloud/app/tests/test_mdt.py (405行)
5. cloud/app/tests/test_agents.py (399行)
6. cloud/app/repositories/mdt_decision_repository.py (384行)
7. cloud/app/services/training_coach_service.py (381行)
8. cloud/app/services/decision_intel_service.py (346行)
9. opportunity/app/repositories.py (329行)
10. cloud/app/tests/test_repositories.py (327行)
11. cloud/app/services/memory_utility_service.py (323行)
12. pharma-intel/app/services/conference_service.py (315行)
13. sales-coach/app/services/reflection_service.py (309行)
14. cloud/app/services/market_intel_service.py (307行)

## 允许的压缩操作（只能做这些）

1. **空行压缩**：函数/类之间保留1个空行（原来是2个），函数体内相邻空行保留0个
2. **Pydantic model 合并**：字段≤3个的 model 类合并为单行定义
3. **长字符串压缩**：多行 f-string/字符串模板合并为单行
4. **注释删除**：删除 `# --- xxx ---` 等装饰性注释行
5. **函数签名行合并**：多行参数签名合并到一行
6. **字典/列表字面量压缩**：多行字典/列表参数合并到1-2行
7. **内联单次调用的辅助函数**：如 `_n404` 这种只被调用1次的小函数
8. **工具函数压缩**：如 `_call_ai` 等工具函数的调用/定义合并

## 禁止的操作

- ❌ 不得修改 import 行
- ❌ 不得修改函数/类签名（参数名、类型注解原样保留，只可合并行）
- ❌ 不得修改控制流（if/for/while/try/except/return/raise/async def/await）
- ❌ 不得修改缩进层级
- ❌ 不得修改变量名或函数名
- ❌ 不得删除必要代码（只可压缩字符串/空行/注释）
- ❌ 不得改变功能逻辑
- ❌ 不得使用批量替换导致不同函数中同名变量相互污染
- ❌ 不得使用 sed/awk 等外部工具，只用 python 编辑

## 验收标准（每个文件压缩后都执行）

1. `wc -l <file>` 显示 ≤ 300
2. `python -c "import ast; ast.parse(open('<file>').read()); print('OK')"` 输出 OK
