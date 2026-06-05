# 任务：修复 FederatedNodesRepository 缺失 + 补全依赖

## 编码准则（18条）
1. Think Before Coding 2. Simplicity First 3. Surgical Changes 4. Goal-Driven Execution 5. 架构优先拒绝补丁 6. 面向组件构建 7. 显式优于隐式 8. 代码整洁自文档化 9. 单一职责 10. 组合优于委托 11. 单一状态源 12. 避免语法糖 13. 命名一致性 14. 文件不超过300行 15. 低耦合(模块间只传ID) 16. 必须用opencode写代码 17. 启动规则(write→TG→confirm→opencode) 18. 完整准则写入每个tasks.md不可省略

## 操作

1. **在 `cloud/app/repositories.py` 添加表定义和Repository类**

在 `TABLE_FEDERATED_ROUNDS_COLS` 定义之后（约第720行附近），添加：
```
TABLE_FEDERATED_NODES_COLS = (
    "id", "node_id", "node_name", "node_type", "organization",
    "status", "endpoint_url", "public_key", "data_summary",
    "last_heartbeat", "round_count", "total_samples",
    "reliability_score", "is_active", "registered_at", "updated_at",
)
```

在 `FederatedRoundsRepository` 类之后，添加：
```
class FederatedNodesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "federated_nodes", TABLE_FEDERATED_NODES_COLS)

    def get_by_node_id(self, node_id: str):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE node_id=?",
            (node_id,),
        ).fetchone()
        return dict(row) if row else None

    def get_all(self):
        return self.list_all()

    def count_active(self):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE status='online'"
        ).fetchone()[0]
```

2. **更新 `cloud/app/repositories/__init__.py`**

在 `from cloud.app.repositories.audit_repository import (` 块中添加：
```
    FederatedNodesRepository,
```

放在 `FederatedRoundsRepository,` 后面。

3. **验证 Cloud 服务能启动**

用 `python -c "from cloud.app.main import app"` 验证导⼊成功。
