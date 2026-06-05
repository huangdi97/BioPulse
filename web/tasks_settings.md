# React 系统设置页面

## 编码准则（必须遵守）
1. Think Before Coding — 先想清楚再写
2. Simplicity First — 简单优先，不过度设计
3. Surgical Changes — 精准改动，不多改
4. Goal-Driven Execution — 目标驱动，不跑偏
5. 架构优先，拒绝补丁 — 先定架构再写代码
6. 面向组件构建 — 组件化开发
7. 显式优于隐式 — 代码清晰可读
8. 代码整洁，自文档化 — 不写多余注释
9. 单一职责 — 一个文件只做一件事
10. 组合优于委托 — 组件组合优先
11. 单一状态源 — 状态不分散
12. 避免语法糖 — 简单直接
13. 命名一致性 — 统一命名风格
14. **文件不超过300行** — 超了必须拆分
15. **低耦合** — 模块间只传ID，不传对象
16. **必须用opencode写代码** — 所有代码通过opencode生成
17. **启动规则: write→TG→confirm→opencode**
18. **完整准则写入每个tasks.md，不可省略**

## 任务

修改 `web/src/pages/settings/SettingsPage.tsx`（替换当前骨架）：

### 左侧导航（设置菜单栏，竖向）：
- 个人信息
- API 配置
- 通知设置
- 关于

### Tab 1: 个人信息
- 头像（圆形占位，显示姓名首字母）
- 姓名（Input）
- 邮箱（Input，只读样式）
- 角色（Badge: 管理员/经理/员工）
- 所属机构（Input）
- 保存按钮

所有字段用 mock 默认值填充。

### Tab 2: API 配置
- 后端地址列表（每行一个后端）：
  - Cloud API: http://localhost:8000
  - Assistant API: http://localhost:8003
  - Opportunity API: http://localhost:8002
  - Sales Assistant API: http://localhost:8004
  - Sales Coach API: http://localhost:8001
- 每行：服务名 + URL（Input）+ 状态指示灯（绿=在线 / 红=离线）
- 测试连接按钮（点击后模拟检查，状态变化）
- 保存按钮

### Tab 3: 通知设置
- 开关列表（用 Toggle/Switch 组件，如果没有就用 Badge 模拟）：
  - 合规预警推送
  - 拜访提醒
  - 任务到期通知
  - 系统公告
  - 每日数据简报
- 每个开关带简短说明

### Tab 4: 关于
- 系统名称：一云四端 · 生命科学销售 AI 工作台
- 版本号：v1.0.0 (Build 2026-06-05)
- 构建信息行
- 设计系统版本：1.0
- 技术支持联系信息

## 验收标准
1. ✅ /settings 页面显示左侧设置菜单 + 右侧内容区
2. ✅ 4个 Tab 均展示内容
3. ✅ API 配置 Tab 有测试连接交互
4. ✅ 文件不超 300 行
5. ✅ TypeScript + Vite 构建通过
