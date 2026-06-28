# Cloud 核心服务

> 一云四端的大脑。承载 Agent 运行时、MCP 工具总线、记忆系统、MDT 多专家会诊、因果推理、合规引擎等全量业务引擎。

**端口：** 8000

## 核心文件

| 目录/文件 | 说明 |
|:----------|:-----|
| `app/main.py` | 应用入口，注册 280+ 路由模块 |
| `app/agent_runtime/` | Agent 运行时（17 文件：Planner/Verifier/Reflector/Pipeline/RuntimeCore） |
| `app/services/` | 95 个业务服务 |
| `app/repositories/` | 21 个数据仓库 |
| `app/seeds/` | 30 个种子数据初始化脚本 |
| `app/routers/` | 扩展路由（24 文件） |
| `app/*_router.py` | 路由模块（50+ 文件） |
| `app/middleware/` | 日志中间件 |
| `langgraph/` | LangGraph 集成 |

## 启动

```bash
uvicorn cloud.app.main:app --port 8000
```
