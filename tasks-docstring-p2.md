# 注释补充 P2：Repository 文件 + Shared 基础设施

## 目标

为数据访问层（Repository）和共享基础设施层补充 docstring，覆盖所有 SQL 查询逻辑。

## 覆盖范围

### P2a：Repository 文件（🔴 最高优先级）

```
cloud/app/repositories/*.py         # 19 个文件，SQL 最密集
cloud/app/repositories.py           # 主仓库文件，2064 行
opportunity/app/repositories.py     # 商机数据访问
opportunity/app/repositories/*.py   # 3 个（bidding/scoring/contact）
sales-coach/app/repositories.py     # 销售教练数据访问
assistant/app/repositories.py       # 助手数据访问
sales-assistant/app/repositories.py # 一线销售数据访问
shared/repository.py                # BaseRepository 基类
```

### P2b：Shared 基础设施（🟡 中等优先级）

```
shared/auth.py                      # 认证逻辑
shared/auth_scope.py                # 权限范围
shared/base.py                      # 基础模型和响应类
shared/compliance.py                # 合规检查
shared/config.py                    # 配置管理
shared/exception_handlers.py        # 异常处理
shared/middleware.py                 # 中间件
shared/notification_client.py       # 通知客户端
shared/rate_limiter.py              # 速率限制
shared/request_id_middleware.py     # 请求ID
shared/structured_logging.py        # 结构化日志
shared/csv_export.py                # CSV 导出
shared/db.py                        # 数据库连接
```

### ❌ 不覆盖

- `columns.py` — 纯列名集合
- `__init__.py` — 空文件
- `conftest_base.py` — 测试配置
- `clinical-ops/`, `patient-engage/`, `market-access/`, `management/` — 冻结尾端，不迭代

## docstring 格式

与之前一致，Google 风格中文。每个 Repository 方法需说明：
- 执行的 SQL 操作类型（增/删/改/查）
- 查询条件
- 返回结构

```python
def get_active_by_id(self, record_id: int) -> Optional[dict]:
    """根据 ID 获取活跃记录。

    Args:
        record_id: 记录 ID

    Returns:
        记录字典，不存在返回 None
    """
```

## 执行策略

1. 复用已有的 `add_docstrings.py` 脚本（上次 OpenCode 生成的），更新 FILE_LIST
2. 添加所有 Repository 和 Shared 文件
3. 运行后 ast.parse + pytest 验证

## 验收标准

1. 所有 Repository 文件的 public 方法有 docstring
2. ast.parse 通过
3. 182 测试全部通过
4. 注释率再提升
