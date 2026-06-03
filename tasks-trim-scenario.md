# 压缩 scenario_library.py (555→≤300行)

## 编码准则

1. Think Before Coding — 先理解再动手
2. Simplicity First
3. Surgical Changes — 精准修改
4. Goal-Driven — 555→≤300行，语法正确可运行
5-12. 保持现有架构
13. 命名一致性 — 不改变量名
14. 文件不超过300行 — 本次目标
15. 低耦合 — 不改变
16. 必须用 opencode 写代码
17. 启动规则 — 已完成写入
18. 完整准则写入每个 tasks.md — ✅

## 允许的压缩操作

1. 空行压缩：函数间1空行，体内0相邻空行
2. 长字符串合并：多行字符串/模板合并为单行
3. 注释删除：装饰性注释
4. 函数签名行合并：多行参数签名合并到一行
5. 字典/列表字面量合并：单层字典/列表参数合并到1行
6. 类定义合并：字段≤3个的 dataclass/class 合并为单行

## 禁止的操作

- ❌ 不得修改 import 行
- ❌ 不得修改函数/类签名（只可合并行）
- ❌ 不得修改控制流
- ❌ 不得修改缩进层级
- ❌ 不得修改变量名
- ❌ 不得删除必要代码
- ❌ 不得改变功能逻辑

## 验收

1. `wc -l sales-coach/app/scenario_library.py` ≤ 300
2. `python -c "import ast; ast.parse(open('sales-coach/app/scenario_library.py').read()); print('OK')"` → OK
