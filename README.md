# 一云四端 · OneCloud4Ends

> 生命科学行业全场景 AI 工作台 — 医药代表拜访管理、商机挖掘、销售助理、销售教练

## 技术栈

**后端** — Python 3.12 / FastAPI / SQLite / LangGraph  
**前端** — React 18 / Vite 6 / TypeScript / Tailwind CSS  
**移动端** — Flutter / Dart / Provider / SQLite (offline-first)  
**AI** — DeepSeek / 多 Agent 运行时 / MCP 工具总线

## 架构

```
一云（Cloud）  ────  四端（Assistant / Opportunity / Sales-Assistant / Sales-Coach）
                        ├── 扩展服务（Management / Pharma-Intel / MarketAccess / ClinicalOps / PatientEngage）
                        └── 移动端（Flutter App）
```

- **一云厚、四端专**：Cloud 承载全量业务引擎，各端专注场景交互
- **独立部署**：各端独立仓库、独立数据库、独立发布
- **故障隔离**：一个端不影响其他，Cloud 停机时四端照常运行（JWT 本地解码）
- **离线优先**：移动端本地 SQLite + 定时同步

## 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Cloud（核心服务）
uvicorn cloud.app.main:app --port 8000

# 启动各端（独立终端）
uvicorn assistant.app.main:app --port 8001
uvicorn opportunity.app.main:app --port 8002
uvicorn sales_assistant.app.main:app --port 8003
uvicorn sales_coach.app.main:app --port 8004

# 启动 Flutter 移动端
cd mobile_app && flutter run
```

## 项目结构

```
one-cloud-four-ends/
├── cloud/                 # Cloud 核心服务（250 文件 / 41K 行）
│   └── app/
│       ├── routers/       # 74 个路由模块
│       ├── services/      # 83 个业务服务
│       ├── repositories/  # 21 个数据仓库
│       ├── schemas/       # 91 张数据库表模型
│       ├── agent_runtime/ # Agent 运行时引擎
│       └── langgraph/     # LangGraph 集成管线
├── assistant/             # 跟台助手（38 文件）
├── opportunity/           # 商机挖掘（34 文件）
├── sales-assistant/       # 销售助理（30 文件）
├── sales-coach/           # 销售教练（29 文件）
├── mobile_app/            # Flutter 移动端
├── frontend/              # React SPA（临时方案）
└── shared/                # 共享模块（auth/compliance/base）
```

## 核心功能

| 模块 | 功能 |
|------|------|
| **AI Agent** | 自主 Agent 运行时（LLM 思考→工具调用→反思循环），支持检查点/审批/断路器/工作队列 |
| **合规引擎** | 全消息类型合规检测 + 决策链 SHA256 审计 |
| **记忆系统** | 类脑六机制记忆（门控/巩固/效用/WorldDB/SAGE/编排器） |
| **因果推断** | 归因评分 + 决策 OSA |
| **MCP 工具总线** | 280 端点统一工具注册与调用 |
| **MDT 会诊** | 多角色 LLM 辩论 → 共识生成 |
| **数字人陪练** | Provider 架构（InternalLLM/WaveCloud/MoShang） |
| **Bidding Agent** | 招标扫描 + AI 决策支持 |
| **离线同步** | 离线优先架构，断网可用，上线自动同步 |

## 测试

```bash
python3 -m pytest cloud/app/tests/ -v
```

## 许可证

MIT
