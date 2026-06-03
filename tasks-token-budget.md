# Layer: token_budget_router.py

## 编码准则（精简版）

1. Think Before Coding — 已读取源文件
2. Simplicity First — 最小改动
3. Surgical Changes — 只改2个文件
4. Goal-Driven — 移除裸SQL，153测试全过
5-15. 不改变架构、不改变签名、不改变model
16. 必须用opencode写代码 ✅
17. 启动规则(write→TG→confirm) ✅ 已确认
18. 完整准则写入每个tasks.md ✅

## 任务

### 文件1：cloud/app/services/token_budget_service.py
在 `get_daily_usage` 方法之后新增：

```python
def count_pending_alerts(self) -> int:
    row = self.db.execute(
        "SELECT COUNT(*) as count FROM token_usage_alerts WHERE alerted = 0",
    ).fetchone()
    return row["count"] if row else 0
```

### 文件2：cloud/app/token_budget_router.py
在 `list_alerts` 端点中，找到这行裸SQL：
```python
row = service.db.execute(
    "SELECT COUNT(*) as count FROM token_usage_alerts WHERE alerted = 0",
).fetchone()
```
替换为：
```python
row = {"count": service.count_pending_alerts()}
```

## 验收

1. python3 -c "import ast; ast.parse(open('cloud/app/token_budget_router.py').read()); print('OK')" → OK
2. python3 -c "import ast; ast.parse(open('cloud/app/services/token_budget_service.py').read()); print('OK')" → OK
