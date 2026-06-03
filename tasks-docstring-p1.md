# Docstring: Router 文件

## 编码准则

1-15. 保持一致
16. 必须用opencode ✅
17. 启动规则 ✅ 已确认
18. 完整准则 ✅

## 任务

为所有 Router 文件的端点函数添加 Google 风格中文 docstring。

### 文件列表

从以下目录的所有 `*_router.py` 文件（不含 `__init__.py`）：

- cloud/app/*_router.py
- cloud/app/routers/*.py
- sales-coach/app/*_router.py
- opportunity/app/*_router.py
- assistant/app/*_router.py
- sales-assistant/app/*_router.py
- pharma-intel/app/*_router.py

### 操作

1. 读取 `add_docstrings.py`，将上述文件添加到 FILE_LIST
2. 运行脚本
3. 全部文件 ast.parse 验证
4. 运行全测试

### 验收

1. 所有 router 文件的 public 函数有 docstring
2. ast.parse 通过
3. 182 测试全过
