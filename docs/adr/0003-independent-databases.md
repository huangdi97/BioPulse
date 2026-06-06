# ADR-0003：一云四端独立数据库

## 日期
2026-05-29

## 状态
已接受

## 背景
项目采用"一云四端"架构（Cloud + Assistant / Opportunity / Sales-Assistant / Sales-Coach）。最初各端共享一个 SQLite 数据库（`cloud.db`），Agent Runtime 也写入同一数据库。这导致：
1. Agent 的中间数据（记忆/状态/快照）与业务数据混在同一个表空间
2. 数据库文件成为单点故障
3. 无法独立部署或扩容

## 决策
**双主线数据隔离**：Cloud 端业务数据写 `cloud.db`，Agent Runtime 数据写 `cloud_agent.db`。四端各端持有独立 SQLite 数据库，通过 Cloud API 通信。

## 理由
- **故障隔离**：Agent 数据异常不影响业务数据
- **独立生命周期**：Agent 记忆可重置而不影响业务
- **部署灵活**：未来可分别迁移到不同数据库引擎（Agent 数据适合 NoSQL，业务数据适合 PG）
- **安全合规**：Agent 运行日志中的用户轨迹与业务数据分离

## 被否决的方案
- **单库 + 表名前缀**：表太多（100+）容易冲突，迁移时更痛苦
- **全量共享数据库**：耦合度太高，修改一个端可能影响其他端
- **立即上 PostgreSQL**：部署和运维成本过高，当前 SQLite 够用

## 后果
- 需要维护 6 个 SQLite 文件（Cloud ×2 + 5端）
- 跨库查询需要通过 API 而非 SQL JOIN
- 未来迁移到 PG 时，每个端各一个 PG 数据库
