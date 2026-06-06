# ADR-0004：Agent 通信平面抽象

## 日期
2026-05-29

## 状态
已接受

## 背景
Agent Runtime 需要与四个端通信（获取业务上下文、查询数据、执行动作）。最初实现为 ToolBridge 直接封装 SQL endpoint（硬编码 IP/端口）和 SQL 查询，导致：
1. Agent 知晓数据库结构，违反 DDD 原则
2. 端口和地址硬编码在代码中
3. 端接口变更时 Agent 代码需要同步修改

## 决策
在 Cloud 端抽象一个 **Agent-Gateway 路由模块**，作为 Agent 与各端之间唯一的通信平面：

```
Agent → Cloud Gateway (8000) → 各端 API
```

ToolBridge 不再持有任何 SQL endpoint 或硬编码 URL，所有外部通信通过 Gateway 路由。

## 理由
- **解耦**：端的内部实现对外部不可见，Agent 不知道端用了 SQLite 还是 PG
- **统一控制**：认证、速率限制、日志追踪在 Gateway 层统一处理
- **可观测**：所有跨端调用流经同一个入口，请求 ID 可串联
- **扩展性**：新增端只需在 Gateway 注册新路由，Agent 零改动

## 被否决的方案
- **Agent 直连端 API**：每端新增/修改接口都要改 Agent 配置
- **消息队列**：当前架构不需要异步通信，增加了不必要的复杂度
- **gRPC**：性能好但调试成本高，当前阶段 HTTP 足够

## 后果
- Gateway 路由模块需要覆盖所有端的关键路由
- 调试时需要追踪 Gateway → 端的调用链
- 性能损耗：每次跨端调用多一跳，但延迟仍在可接受范围内
