# Docstring: 非 Cloud 服务的 Service 文件

## 编码准则

1-15. 保持一致
16. 必须用opencode ✅
17. 启动规则 ✅ 已确认
18. 完整准则 ✅

## 任务

为以下目录中所有 Python 文件的每个 public 方法添加 Google 风格中文 docstring：

- sales-coach/app/services/*.py (11 个文件)
- opportunity/app/services/*.py (12 个文件)
- assistant/app/services/*.py (13 个文件)
- sales-assistant/app/services/*.py (12 个文件)
- pharma-intel/app/services/*.py (6 个文件)

### 规则

1. 每个 `def` 方法（不含 `def _` 开头的私有方法）添加 docstring
2. 每个 `class` 定义添加类 docstring
3. 格式：
   ```python
   def method_name(self, param1, param2) -> return_type:
       """中文描述方法功能。

       Args:
           param1: 参数说明
           param2: 参数说明

       Returns:
           返回值说明
       """
   ```
4. 已有 docstring 的方法跳过（不修改）
5. 不修改任何功能代码
6. 每个文件修改后 ast.parse 验证
7. 最后运行全测试

### 验收

1. 所有 service 文件的 public 方法有 docstring
2. ast.parse 全部通过
3. pytest 182 passed
