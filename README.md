# 一云四端 · Cloud API

面向**医药+生物双主线**的智能 CRM SaaS 平台。一云（Cloud API）承载全部业务引擎，四端（Assistant / Opportunity / Sales-Assistant / Sales-Coach）按职责分发。

## 架构概览

```
┌──────────────────────────────────────────────────┐
│                  Cloud API (8000)                │
│  认证 │ 合规 │ 商机 │ 拜访 │ Agent │ MDT │ 记忆   │
│  知识图谱 │ 因果推理 │ 团队 │ 审计 │ 导出 │ 配置   │
│          ┌─────────── 双主线隔离 ───────────┐    │
│          医药线 (pharma)     科研线 (research)  │
│          JWT scope: pharma   JWT scope: research │
│          独立规则库+审计链    独立规则库+审计链    │
└──────────────────────┬───────────────────────────┘
                       │
    ┌──────────┬───────┼────────┬──────────────┐
    │          │       │        │              │
 Assistant  Opport.  SalesAsst  SalesCoach    ...(Flutter)
 (8003)    (8002)   (8004)    (8001)
```

## 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| 运行时 | Python 3.12 + FastAPI | ASGI 异步框架 |
| 数据库 | SQLite（开发）/ PostgreSQL（生产） | 双模式支持，环境变量切换 |
| AI Agent | LangGraph | 状态机、可中断/恢复、Token追踪 |
| 合规引擎 | 数据驱动 (JSON rules) | 新增规则无需改代码 |
| API 文档 | OpenAPI / Swagger | 访问 /docs 交互式文档 |
| CI/CD | GitHub Actions (pytest + benchmark) | 性能基线自动比较 |
| 测试 | pytest + pytest-benchmark | 62+ 测试用例，含集成和 E2E |

## 核心特性

### 1. 双主线物理隔离
医药代表拜访管理和科研销售线索管理在同一平台上物理隔离：
- 独立数据库（`cloud.db` / `research.db`）
- 独立 JWT scope（`pharma` / `research`）
- 独立合规规则库（`pharma_rules.json` / `research_rules.json`）
- 独立审计链
- 代码审查验证无跨模式 SQL JOIN

### 2. 数据驱动合规引擎
- 5 条 L1 硬红线规则（备案身份核验、统方、回扣、利益输送、场所异常）
- 3 条科研线规则
- 规则文件 JSON 格式，新增规则无需改代码
- 仪表板展示拦截统计

### 3. 多专家会诊系统（MDT）
- 多位 AI Agent 以辩论形式分析复杂决策
- Analyst（分析师）、Explorer（探索者）、Critic（评论家）、Judge（裁判）四角色
- LangGraph 状态机保证执行可回溯

### 4. 可信 AI 框架
- 记忆门控与巩固
- 世界树知识推理
- 因果推理引擎
- 隐私计算（差分隐私 + 联邦学习）

## 快速启动

```bash
# 1. 克隆
git clone https://github.com/your-org/one-cloud-four-ends.git
cd one-cloud-four-ends

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库
python -c "from cloud.app.database import init_db; init_db()"
python -c "from cloud.app.research_database import init_research_db; init_research_db()"

# 5. 启动
venv/bin/uvicorn cloud.app.main:app --host 0.0.0.0 --port 8000

# 访问 http://localhost:8000/docs 查看 API 文档
```

## 项目结构

```
one-cloud-four-ends/
├── cloud/           # Cloud API（业务引擎中心，179文件）
│   └── app/
│       ├── main.py           # 入口 + 中间件 + 路由注册
│       ├── database.py       # 数据库连接管理
│       ├── schema.py         # 87张表 CREATE TABLE SQL
│       ├── routers/          # 路由（29+ 文件）
│       ├── services/         # 业务逻辑层（56 个 Service 类）
│       ├── repositories/     # 数据访问层（19 文件，桥接旧文件）
│       └── tests/            # 62 个测试
├── shared/         # 共享基础设施
│   ├── base.py, auth.py, middleware.py
│   ├── repository.py, csv_export.py
│   └── models/
├── assistant/      # 全能助理端 (8003)
├── opportunity/    # 商机挖掘端 (8002)
├── sales-assistant/ # 销售助手端 (8004)
├── sales-coach/    # 销售教练端 (8001)
└── frontend/       # React SPA（前管理端界面）
```


## 测试

```bash
# 运行全部测试
python -m pytest cloud/app/tests/ -v

# 代码风格检查
pre-commit run --all-files
```

## 许可证

MIT
