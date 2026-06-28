# 前端开发说明

## 当前状态

当前目录包含一个 **React SPA**（Vite + TypeScript + Tailwind + Radix UI），仅用于开发调试。后续将全部替换为 **Flutter App**，请 Flutter 外包团队按本文件需求开发。

---

## 双模式架构

系统支持两种业务模式，由顶部按钮切换，业务层完全隔离：

| 特性 | 拜访模式 (visit) | 科研模式 (research) |
|------|------------------|---------------------|
| JWT scope | `visit` | `research` |
| 目标用户 | 医药代表 | 科研销售 |
| 核心流程 | HCP列表→拜访录入→合规提示→任务列表 | PI线索→科研画像→产品匹配→报价单 |
| 数据表 | hcp_profiles, visits, compliance_rules | pi_profiles, products, pubmed_cache |

切换模式时前端应重新获取对应 scope 的 JWT token。

---

## Flutter App 需求

### 登录
- JWT 认证（`/auth/login` 获取 access_token + refresh_token）
- Token 刷新（`/auth/refresh`）
- 存储 token 到本地安全存储

### 拜访模式 (mode:visit)
1. **HCP 列表** — 搜索/筛选医生，查看详情
2. **拜访录入** — 填写拜访记录（照片上传、位置签到）
3. **合规提示** — 提交前展示合规规则检查结果（pharma_rules L1 硬红线）
4. **任务列表** — 查看待办任务

### 科研模式 (mode:research)
1. **PI 线索列表** — 搜索 Principal Investigator
2. **科研画像** — PI 详情（论文数、h-index、研究领域）
3. **产品匹配** — 搜索产品知识库（FBS 胎牛血清等）
4. **报价单** — 产品详情与价格

---

## 后端 API 列表

### 认证
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/register` | 注册（username, password） |
| POST | `/auth/login` | 登录，返回 access_token + refresh_token |
| POST | `/auth/refresh` | 刷新 token |

### 用户
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/users/{id}` | 用户详情 |
| POST | `/users` | 创建用户 |
| GET | `/users` | 用户列表 |

### 合规 (Compliance)
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/compliance/check` | 内容合规检查 |
| POST | `/compliance/rules` | 创建合规规则 |
| GET | `/compliance/rules` | 规则列表 |
| DELETE | `/compliance/rules/{id}` | 删除规则 |
| POST | `/compliance-v2/scan` | V2 合规扫描 |
| GET | `/compliance-v2/dashboard` | 合规仪表板 |
| GET | `/compliance-v2/records` | 审计记录列表 |
| GET | `/compliance-v2/records/{id}` | 审计记录详情 |

### PI 科研画像
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/pi/search?q=` | 搜索 PI（支持姓名/机构/研究领域模糊匹配） |
| GET | `/api/pi/{id}` | PI 详情 |
| POST | `/api/pi` | 创建 PI |
| PUT | `/api/pi/{id}` | 更新 PI |

### 产品知识库
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/products/search?q=&category=` | 搜索产品 |
| GET | `/api/products/{id}` | 产品详情 |
| POST | `/api/products` | 创建产品（管理员） |

### PubMed 搜索
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/pubmed/search` | 搜索论文（body: {keyword, max_results?}) |
| POST | `/api/pubmed/author/{name}` | 按作者搜索论文 |

### LangGraph
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/langgraph/test` | 执行测试 Graph |

### 仪表板
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/dashboard/overview` | 总览 |
| GET | `/dashboard/users` | 用户统计 |
| GET | `/dashboard/compliance` | 合规统计 |
| GET | `/dashboard/contents` | 内容统计 |

### 内容管理
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/contents` | 创建内容 |
| GET | `/contents` | 内容列表 |
| GET | `/contents/{id}` | 内容详情 |
| PATCH | `/contents/{id}` | 更新内容 |
| DELETE | `/contents/{id}` | 删除内容 |

### 通知
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/notifications` | 通知列表 |
| GET | `/notifications/unread-count` | 未读数 |

### 更多端点
完整 API 文档请参考后端 Swagger UI（开发服务器启动后访问 `/docs`）。

---

## 开发说明

1. **后端地址**: `http://localhost:8000`
2. **Swagger 文档**: `http://localhost:8000/docs`（后端未完成时可先用 Swagger 调试）
3. **JWT 认证**: 所有业务接口需在 Header 传 `Authorization: Bearer <token>`
4. **开发启动**: 后端 `python -m cloud.app.main`，前端 `npm run dev`

---

*本文档由 Flutter 外包团队按此需求开发，如有疑问请联系后端团队。*
