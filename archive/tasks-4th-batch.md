# 第4批执行任务 · 合规白屏修复 + 经理端/代表端分离

## 编码准则（18条·完整版）
1. Think Before Coding
2. Simplicity First
3. Surgical Changes
4. Goal-Driven Execution
5. 架构优先，拒绝补丁
6. 面向组件构建
7. 显式优于隐式
8. 代码整洁，自文档化
9. 单一职责
10. 组合优于委托
11. 单一状态源
12. 避免语法糖
13. 命名一致性
14. 文件不超过300行（含300）
15. 低耦合（模块间只传ID）
16. 必须用 OpenCode 写代码
17. 启动规则：write→TG文档→confirm→opencode
18. 完整准则写入每个 tasks.md 不可省略

---

## 4A：合规看板后端服务+路由（新建2文件，修改1文件）

### 后端服务：`cloud/app/services/compliance_service.py`

**功能：** 提供合规 dashboard 数据，返回前端 ComplianceDashboard 类型期望的格式：
```typescript
{
  todayViolations: number,
  weeklyTotal: number,
  processedRate: number,
  highRiskCount: number,
  dailyTrend: { date: string; count: number }[],
  topCategories: { category: string; count: number; percentage: number }[],
  topReps: { repName: string; violationCount: number; riskLevel: string }[]
}
```

**实现：**
- 类 `ComplianceService`，构造函数接收 db Session
- 方法 `dashboard()` → 查询 visits 表的合规扫描数据聚合
  - `todayViolations` = 今天违规数（`compliance_status != 'passed'`）
  - `weeklyTotal` = 近7天总违规数
  - `processedRate` = 已处理违规/总违规 × 100
  - `highRiskCount` = 高风险违规数
  - `dailyTrend` = 近7天每天违规数（日期格式 `MM-DD`）
  - `topCategories` = 按违规类型分组TOP3（类别名从 violations JSON 提取）
  - `topReps` = 按代表名分组违规数TOP3（含风险等级）
- 所有聚合用 SQLite SQL 查询实现（group by, count, date 函数）
- 数据不足时返回模拟默认值（不要空数组引起 recharts 报错）

**技术栈约束：**
- 使用 `from sqlalchemy import text` 执行原生SQL
- 返回类型 `dict`（不创建新schema类）
- 文件 ≤ 80 行

### 后端路由：`cloud/app/routers/compliance_router.py`

**功能：** 注册合规相关API端点

**实现：**
- 创建 APIRouter，prefix 空（手动注册 `/api/cloud/compliance-v2/`）
- `GET /api/cloud/compliance-v2/dashboard` → 调用 ComplianceService.dashboard()
- `POST /api/cloud/compliance-v2/scan` → 接收 `{content: string}`，返回模拟扫描结果（使用前端原有的 `keywordRules` 逻辑简化版）
- `GET /api/cloud/compliance-v2/records` → 分页查询违规记录列表
- `GET /api/cloud/compliance-v2/records/{id}` → 单条违规详情
- 所有响应格式 `{code: 0, message: "success", data: ...}`
- 使用 `from fastapi import Depends` + `get_db` 获取 session

**技术栈约束：**
- 文件 ≤ 100 行
- 路由复用现有的 `get_db` 依赖

### 后端注册：`cloud/app/main.py`

**修改：**
- 在 `app.include_router(...)` 区域增加：`app.include_router(compliance_router)`
- 导入 compliance_router

**技术栈约束：**
- 修改 ≤ 2 行

---

## 4B：合规看板前端健壮性（修改1文件）

### 前端：`frontend/src/pages/manager/ComplianceOverview.tsx`

**修改：**
- useEffect 中的 `fetchComplianceDashboard().then(...)` 改为带 `.catch()` 的 async/await
- 添加 React ErrorBoundary 包裹整个组件（在组件文件内定义内联 ErrorBoundary 类组件，用 `componentDidCatch` 捕获渲染异常并显示友好提示）
- 确保 loading 状态在 catch 时也被置为 false

**技术栈约束：**
- React + TypeScript
- 文件 ≤ 300 行（当前171行，加ErrorBoundary预计到200行）

---

## 4C：角色路由守卫（新建1文件，修改4文件）

### 后端角色：`cloud/app/services/auth_service.py`

**修改：**
- `create_access_token` 函数 payload 中加 `role` 字段
- 从数据库用户记录中读取 role（默认 `'rep'`）
- token 校验时返回 role

### 后端角色：`cloud/app/routers/auth_router.py`

**修改：**
- 登录API `/auth/login` 返回体加 `role` 字段
- 从 token payload 提取 role

### 后端角色：`cloud/app/models/` 下添加迁移脚本

**新建 `cloud/app/models/migration_add_role.py`：**
- 检查 `users` 表是否有 `role` 列
- 没有则 `ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'rep'`
- 给现有 admin 用户设 role='admin'
- 使用 SQLite ALTER TABLE 语法

### 前端角色类型：`frontend/src/types/index.ts`

**修改：**
- `User` 接口加可选字段 `role?: string`

### 前端角色路由守卫：`frontend/src/components/RoleRoute.tsx`

**新建：**
- 类组件或函数组件，检查 `AuthContext` 中 user.role
- 接收 `allowedRoles: string[]` prop
- 用户角色不在 allowedRoles 中时 → 显示"无权限"提示 + 3秒后重定向到对应端首页
- admin 角色可访问所有端

### 前端Auth上下文：`frontend/src/contexts/AuthContext.tsx`

**修改：**
- login 成功后存储 `user.role`（从 login API 返回中提取）
- `User` 对象包含 role 字段

### 前端路由：`frontend/src/App.tsx`

**修改：**
- `/rep/*` 路由用 `RoleRoute` 包裹，allowedRoles 包含 `['rep', 'admin']`
- `/manager/*` 路由用 `RoleRoute` 包裹，allowedRoles 包含 `['manager', 'admin']`
- 登录成功后 navigate 按角色跳转（auth context 中实现）

### 前端登录页：`frontend/src/pages/Login.tsx`

**修改：**
- 登录成功后，根据 `user.role` 跳转
  - `rep` → `/rep/dashboard`
  - `manager` → `/manager/dashboard`
  - `admin` → `/manager/dashboard`

---

## 4D：构建+部署

### 前端构建
- `cd /home/hermes/one-cloud-four-ends/frontend && npx vite build`
- 确认零错误零warning
- 将 `dist/` 复制到后端 `cloud/static/`

### 后端重启
- 执行 db migration（users 表加 role 列）
- 重启 main.py
- 验证所有端正常访问

---

## 执行顺序

1. **4A-后端服务** → `cloud/app/services/compliance_service.py`
2. **4A-后端路由** → `cloud/app/routers/compliance_router.py`
3. **4A-后端注册** → `cloud/app/main.py`（+2行）
4. **4A-验证** → 手动 curl 测试 dashboard 端点
5. **4B-前端健壮性** → `ComplianceOverview.tsx`
6. **4C-后端角色** → auth 相关文件修改 + migration
7. **4C-前端角色** → RoleRoute.tsx + AuthContext.tsx + App.tsx + Login.tsx
8. **4D-构建+部署** → vite build + 迁移 + 重启

## 验收标准

详见执行文档第4批-合规白屏修复+端分离.md
