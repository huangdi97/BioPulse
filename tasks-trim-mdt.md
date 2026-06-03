# 压缩 mdt_engine_router.py → ≤300 行

## 准则（以下18条编码准则永久有效，必须遵守）

1. Think Before Coding — 先理解再动手
2. Simplicity First — 用最简单的方式实现
3. Surgical Changes — 精准修改，不碰不相干代码
4. Goal-Driven Execution — 目标导向：384→≤300行，语法正确可运行
5. 架构优先，拒绝补丁 — 不改变架构
6. 面向组件构建 — 不适用
7. 显式优于隐式 — 保持代码可读性
8. 代码整洁，自文档化 — 保留必要注释
9. 单一职责 — 不改变
10. 组合优于委托 — 不适用
11. 单一状态源 — 不适用
12. 避免语法糖 — 保持原样
13. 命名一致性 — 不改变量名
14. 文件不超过300行 — 这是本次目标
15. 低耦合 — 不改变
16. 必须用 opencode 写代码 — 本任务由 opencode 执行
17. 启动规则 — 已完成写入
18. 完整准则写入每个 tasks.md — ✅

## 任务

压缩 `cloud/app/mdt_engine_router.py` 从当前384行到≤300行，同时保持代码语法正确且功能不变。

## 允许的压缩操作（只能做这些）

1. **空行压缩**：函数/类之间保留1个空行（原来是2个），函数体内相邻空行保留0个
2. **Pydantic model 合并**：字段≤3个的 model 类合并为单行定义
3. **长字符串压缩**：多行 f-string/字符串模板合并为单行
4. **注释删除**：删除 `# --- endpoints ---` 等注释行
5. **函数签名行合并**：`@router.xxx` 后面的多行参数签名合并到一行
6. **`_n404` 函数内联**：该函数只被 `get_session` 调用1次，可直接内联
7. **`_call_ai` 压缩**：合并 urllib.request 创建和调用为更紧凑的写法
8. **JSON 格式字符串压缩**：debate 和 consensus 中的 JSON 模板字符串合并为单行

## 禁止的操作

- ❌ 不得修改任何 import 行
- ❌ 不得修改任何函数/类的签名（只可合并参数行，不可删除参数）
- ❌ 不得修改任何控制流（if/for/try/except/return/raise）
- ❌ 不得修改任何缩进层级
- ❌ 不得修改变量名
- ❌ 不得删除必要代码（只可压缩字符串和空行）
- ❌ 不得改变功能逻辑

## 验收标准

1. 文件行数 ≤ 300
2. `python -c "import ast; ast.parse(open('cloud/app/mdt_engine_router.py').read()); print('OK')"` 输出 OK
3. cd /home/hermes/one-cloud-four-ends && python -m pytest cloud/app/tests/test_cloud.py -x -q 2>&1 | tail -5 显示通过
