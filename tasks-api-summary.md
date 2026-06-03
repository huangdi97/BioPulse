# 给所有 FastAPI 端点添加 OpenAPI summary

## 准则（18条，精简版）

1-13. 保持现有代码质量和架构
14. 文件不超过300行 — 不改变
15. 低耦合 — 不改变
16. 必须用 opencode 写代码
17. 启动规则 ✅
18. 完整准则写入每个 tasks.md ✅

## 任务

扫描以下目录中所有 `*_router.py` 文件，给每个 `@router.` 装饰器添加 `summary=` 参数。

### 目标文件范围

```
cloud/app/*_router.py
cloud/app/routers/*.py
assistant/app/*_router.py
opportunity/app/*_router.py
sales-coach/app/*_router.py
sales-assistant/app/*_router.py
pharma-intel/app/*_router.py
```

### 转换规则

对每个不包含 `summary=` 的 `@router.{get,post,put,patch,delete}(...)` 装饰器，在参数中添加 `summary=`：

| 函数名模式 | 生成的 summary |
|:---|:---|
| `list_xxx` / `get_all_xxx` | "List all {xxx}" |
| `get_xxx` / `get_xxx_by_id` | "Get {xxx} by ID" |
| `create_xxx` | "Create {xxx}" |
| `update_xxx` / `patch_xxx` | "Update {xxx}" |
| `delete_xxx` / `remove_xxx` | "Delete {xxx}" |
| `search_xxx` / `find_xxx` / `query_xxx` | "Search {xxx}" |
| `count_xxx` / `stat_xxx` | "Count/stat {xxx}" |
| `debate` / `consensus` | Use function docstring or "Run MDT debate" / "Generate consensus" |
| `dashboard` | "Get dashboard data" |
| `health` | "Health check" |
| 其他动词+名词 | "Verb Noun" (标题格式化) |

### 具体规则

1. 只添加 `summary=` 参数，不修改任何其他内容
2. 如果装饰器已有 `summary=` 参数，跳过
3. summary 值用双引号包裹
4. 中文端点的 summary 也用中文（如果端点名称是中文的）
5. 保持原装饰器的所有其他参数不变
6. 每个文件修改后运行 python -c "import ast; ast.parse(open('file').read()); print('OK')" 验证语法

### 示例

```python
# 修改前
@router.get("/sessions", response_model=...)
def list_sessions(...):

# 修改后
@router.get("/sessions", response_model=..., summary="List MDT sessions")
def list_sessions(...):
```

### 验收标准

1. 所有 router 文件语法正确（ast.parse 通过）
2. 每个 @router 装饰器都有 summary= 参数（或原本就有）
3. 测试全部通过
