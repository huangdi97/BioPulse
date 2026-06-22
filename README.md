# BioPulse — 生命科学行业 Agent-native 工作台

> 不是"加了 AI 的 CRM"。是 Agent 替代表干活、替经理看数据、替总裁做推演。

## 什么让 BioPulse 不同

| 传统 CRM | BioPulse |
|---|---|
| 人填表、人查数据 | Agent 自动填表、主动推异常 |
| 看报表猜趋势 | 推演器给因果链 + 预测区间 + 平行对比 |
| 合规靠抽查 | 全息稽核 7×24 无人值守 |
| 问 IT 要数据 | 直接问 Agent，"上周生物线商机转化怎么样" |

## 核心能力

- **7 个专业 Agent** — 合规监控、异常分析、销售建议、销售教练、情报、知识、MDT
- **推演器** — 因果链 + 置信度 + 回溯验证 + 平行对比
- **代表工作台** — 拜访排序、HCP画像、竞品推送、语音填表、费用预审、拜访理由
- **多端覆盖** — 管理端(React)、移动端(Flutter Android/iOS)、Web端、微信小程序
- **全息稽核 合规** — 拜访×费用×流向交叉稽核 + 飞检 + 窜货检测
- **生产就绪** — Prometheus+Grafana、Nginx+TLS、每日备份、CI/CD

## 架构

```
Cloud(8000) ── Agent Runtime(L4循环) ── 7 Agent ── 多端
    │                                              ├── 管理端 (React)
    │                                              ├── 移动端 (Flutter)
    │                                              ├── Web端 (React)
    │                                              └── 微信小程序
    │
    ├── 合规引擎     ├── 推演器         ├── 记忆系统
    ├── MCP 工具总线  ├── 因果推断       └── 事件总线
```

## Quick Start（5 分钟）

**依赖：** Python 3.12、PostgreSQL（可选，默认 SQLite）、API Key（DeepSeek / OpenAI）

```bash
# 1. 克隆仓库
git clone https://github.com/huangdi97/BioPulse.git
cd BioPulse

# 2. 创建虚拟环境并安装依赖
python -m venv venv && source venv/bin/activate
pip install -r cloud/requirements.txt

# 3. 配置环境变量
cp .env.example .env   # 填入 DEEPSEEK_API_KEY 等必要配置

# 4. 初始化数据库并启动 Cloud
python -c "from cloud.app.database import init_db; init_db()"
uvicorn cloud.app.main:app --reload --port 8000

# 5. 查看 Agent 运行（新终端）
curl http://localhost:8000/agent-gateway/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_key":"analyst","goal":"分析最近的拜访数据"}' | python -m json.tool

# 6. 启动管理端（新终端）
cd frontend && npm install && npm run dev

# 7. 启动 Flutter 移动端（新终端）
cd mobile_app && flutter run
```

> 使用 Docker 一键部署见 `docker-compose up -d`。

## 开发

| 层 | 技术 |
|---|---|
| 后端 | Python 3.12 / FastAPI / SQLite / LangGraph / Agent Harness |
| 前端 (管理端/Web端) | React 18 / Vite 6 / TypeScript / Tailwind CSS |
| 移动端 | Flutter / Dart / Provider / SQLite (offline-first) |
| AI | DeepSeek / 多 Agent 运行时 / MCP 工具总线 / MDT 多专家会诊 |
| 监控 | Prometheus + Grafana |
| CI/CD | GitHub Actions |

## 项目结构

```
one-cloud-four-ends/
├── cloud/                 # Cloud 核心服务（290+ 文件 / 280 路由）
│   └── app/
│       ├── agent_runtime/ # Agent 运行时引擎（17 文件）
│       ├── inference/     # 推演器（因果/假设/验证/模式发现）
│       ├── services/      # 95 个业务服务
│       ├── repositories/  # 21 个数据仓库
│       └── seeds/         # 30 个种子数据脚本
├── assistant/             # 跟台助手（36 文件）
├── opportunity/           # 商机挖掘（33 文件）
├── sales-assistant/       # 销售助理（28 文件）
├── sales-coach/           # 销售教练（33 文件）
├── pharma_intel/          # 制药情报（17 文件）
├── management/            # 管理端（12 文件）
├── mobile_app/            # Flutter 移动端
├── web/                   # React Web 端
├── frontend/              # React SPA（管理端）
├── shared/                # 共享模块（auth/compliance/base）
├── design-tokens/         # 统一设计系统 Token
└── docs/                  # 设计文档与指南
```

## 测试

```bash
python3 -m pytest cloud/app/tests/ -v
```

## License

MIT
