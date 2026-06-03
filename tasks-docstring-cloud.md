# Docstring: Cloud Service 文件

## 编码准则

1-15. 保持一致
16. 必须用opencode ✅
17. 启动规则 ✅ 已确认
18. 完整准则 ✅

## 任务

为 cloud/app/services/*.py 中所有 public 方法添加 Google 风格中文 docstring。

### 操作

1. 读取 `add_docstrings.py` 脚本，理解其模式
2. 将 `cloud/app/services/` 下所有 `.py` 文件（不含 `__init__.py` 和 `base.py`）添加到脚本的 FILE_LIST 中
3. 运行脚本
4. 全部文件 ast.parse 验证
5. 运行 `python -m pytest cloud/app/tests/ -q --no-cov` 验证

### 格式

已有 docstring 的跳过。class 加类 docstring，def 加方法 docstring（不含 `def _` 开头的）。

### 验收

1. 所有 Cloud service 文件 public 方法有 docstring
2. ast.parse 通过
3. 153 个 Cloud 测试通过
