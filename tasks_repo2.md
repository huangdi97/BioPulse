# 任务：补全缺失的 Repository 类

## 编码准则（18条）
1. Think Before Coding 2. Simplicity First 3. Surgical Changes 4. Goal-Driven Execution 5. 架构优先拒绝补丁 6. 面向组件构建 7. 显式优于隐式 8. 代码整洁自文档化 9. 单一职责 10. 组合优于委托 11. 单一状态源 12. 避免语法糖 13. 命名一致性 14. 文件不超过300行 15. 低耦合(模块间只传ID) 16. 必须用opencode写代码 17. 启动规则(write→TG→confirm→opencode) 18. 完整准则写入每个tasks.md不可省略

## 背景
新注册的 12 个孤儿路由暴露了两个缺失的 Repository 类：
1. `AuditChainBlocksRepository` — trust_audit_router 依赖
2. `FederatedNodesRepository` — 已补（但需挪到独立文件）

FileNotFound错误链：trust_audit_router → trust_audit_service → 找不到 AuditChainBlocksRepository

## 操作

### 1. 在 `cloud/shared/columns.py` 添加表定义

在 `TABLE_FEDERATED_NODES_COLS` 之后添加：

```
TABLE_AUDIT_CHAIN_BLOCKS_COLS = [
    "id",
    "block_hash",
    "prev_block_hash",
    "block_data",
    "block_type",
    "created_by",
    "node_id",
    "timestamp",
]
```

### 2. 在 `cloud/app/repositories/audit_repository.py` 添加 AuditChainBlocksRepository

导入 `TABLE_AUDIT_CHAIN_BLOCKS_COLS`，然后在 FederatedNodesRepository 类之后添加：

```
class AuditChainBlocksRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "audit_chain_blocks", TABLE_AUDIT_CHAIN_BLOCKS_COLS)

    def get_latest(self):
        row = self.db.execute(
            f"SELECT {', '.join(self.cols)} FROM {self.table_name} ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None

    def get_chain(self, node_id: str = "", limit: int = 50):
        if node_id:
            rows = self.db.execute(
                f"SELECT {', '.join(self.cols)} FROM {self.table_name} WHERE node_id=? ORDER BY id DESC LIMIT ?",
                (node_id, limit),
            ).fetchall()
        else:
            rows = self.db.execute(
                f"SELECT {', '.join(self.cols)} FROM {self.table_name} ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
```

### 3. 在 `cloud/app/repositories/__init__.py` 导出 AuditChainBlocksRepository

在 `FederatedNodesRepository,` 之后添加 `AuditChainBlocksRepository,`

### 4. 验证

用 `python -c "from cloud.app.repositories import AuditChainBlocksRepository, FederatedNodesRepository; print('OK')"` 验证

### 5. 然后启动 Cloud 服务测试

用 uvicorn cloud.app.main:app --port 8001（测试端口避免冲突）验证能启动
