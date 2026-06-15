# Phase 5 收尾执行计划（补充版）

> 目标：完成剩余所有未做项，使项目各维度闭合。
> **共 10 批次**（原 5 批 + 5 批新发现缺口）
> 顺序：先低风险大批量 → 后高风险重构

---

## 批次 C-1：Docstring 统一补齐

**波及范围：** cloud/app/services/ 下 7 个文件
**工作量：** 小（纯注释，无逻辑改动）
**风险：** 极低

| 文件 | 函数数 | 当前 docstring | 动作 |
|:-----|:------:|:--------------:|:-----|
| `agent_core.py` | 21 | 0 | 全补 |
| `decision_intel_service.py` | 15 | 2 | 补13 |
| `memory_retriever.py` | 11 | 2 | 补9 |
| `kg_service.py` | 10 | 2 | 补8 |
| `asr_service.py` | 9 | 4 | 补5 |
| `decision_logger.py` | 9 | 2 | 补7 |
| `intel_collector.py` | 9 | 2 | 补7 |

**验收：** ruff + pytest 通过，无新增 warning

---

## 批次 C-2：子项目测试覆盖补齐

**波及范围：** 7 个子项目
**工作量：** 中
**风险：** 低（测试不碰业务逻辑）

| 子项目 | 当前测试数 | 目标测试数 | 新增内容 |
|:-------|:----------:|:----------:|:---------|
| clinical-ops | 1 | 4 | 路由+服务+审批流 |
| patient-engage | 1 | 4 | 患者端+通知 |
| market-access | 1 | 4 | 准入路由+策略 |
| management | 2 | 4 | 用户管理+配置 |
| pharma_intel | 3 | 5 | 情报分析+监控 |
| assistant | 4 | 6 | 离线录音+审批 |
| sales-coach | 6 | 7 | 训练评分 |

**验收：** 各子项目 `-k "$subproject"` 全绿

---

## 批次 C-3：Flutter 测试补齐

**波及范围：** `mobile_app/test/`
**工作量：** 小
**风险：** 低

现有 3 个测试（visit_list_priority_test, visit_recording_test, widget_test）。
新增：api_clients 测试、model 测试、状态管理测试。

**验收：** `flutter test` 全绿

---

## 批次 C-4：WeApp 骨架补全

**波及范围：** `weapp/`
**工作量：** 中
**风险：** 中（前端无单测）

现有骨架：3 页（index/compliance/visit）+ utils（api.js/auth.js）
缺口（对照 design.md 第9章前端规划）：
1. 缺 market-access 详情页
2. 缺 patient profile 页
3. 缺 agent insight bar 组件
4. 缺离线缓存状态页

**验收：** 对照 design.md §9 前端章节，逐项确认不缺页

---

## 批次 C-5：runtime_core Mixin → 组合模式重构

**波及范围：** 6 文件（820 行总计）
**工作量：** 大
**风险：** 高

**当前状态：**
```
RuntimeCore 继承链：
  ExecutionLoopMixin     (202L)
  RollbackHandlerMixin   (46L)
  RuntimeHelper          (128L)
  RuntimeLLM
  RuntimeCoreToolsMixin  (57L)
  RuntimeToolExecMixin   (162L)
```

**目标：** 每个 Mixin 拆为独立组件 + RuntimeCore 通过组合持有实例

**策略：** 不做一步到位重构，分 3 小步：
1. 先提取最小依赖的（RuntimeCoreToolsMixin, RuntimeHelper → 纯函数工具类）
2. 再提取 RuntimeToolExecMixin → ToolExecutor 类
3. 最后提取 ExecutionLoopMixin → 需处理 callback 注入

**验收：** agent_runtime 全部测试 + cloud 全部测试通过

---

## 补充批次（新发现缺口）

---

## 批次 C-6：web/ 前端测试补齐

**波及范围：** `web/src/`（38个 ts/tsx 文件，零测试）
**工作量：** 中
**风险：** 低

**缺口：** 另一个前端站点 `web/` 完全无测试覆盖。frontend/ 已有 4 个 vitest 测试文件，但 web/ 甚至没有配 test 命令。

**动作：**
1. `package.json` 加 test 脚本（vitest）
2. 覆盖核心页面：至少 3 个组件测试（登录/仪表盘/情报）

**验收：** `cd web && npx vitest run` 通过

---

## 批次 C-7：CI 部署自动化

**波及范围：** `.github/workflows/ci.yml`
**工作量：** 小
**风险：** 低

**缺口：** design.md §17.11 标记 "CI部署阶段被注释" 为 P1。当前 ci.yml 只有 `pytest` 一个 step，没有部署。

**动作：**
1. 补充 deploy job：build Docker → scp → systemd restart（或 ssh deploy 脚本）
2. 用环境变量保护生产仓库（只 master 分支触发部署）

**验收：** 合并 master 后自动部署到服务器（dry-run 验证路径正确）

---

## 批次 C-8：竞品监控前端页面

**波及范围：** pharma_intel 前端看板
**工作量：** 中
**风险：** 低

**缺口：** design.md §9 标记 "竞品监控前端" 为 P0。舆情看板（趋势折线图+情绪分析+声量对比）未实现。

**动作：**
1. 在 pharma_intel 前端（或 web/）添加舆情 dashboard 页
2. 后端已有爬虫/舆情数据（crawler/models.py），前端消费 API

**验收：** 后端竞品数据可在前端展示趋势/情绪/声量

---

## 批次 C-9：清理 agents/ 空目录

**波及范围：** `agents/`
**工作量：** 极小
**风险：** 极低

**动作：** 删除空目录，或在其中放一个 `.gitkeep` + README 说明用途

---

## 批次 C-10：README 一致性检查

**波及范围：** 13 个 README.md
**工作量：** 小
**风险：** 低

**动作：**
1. 快速扫描每个 README 的 "last updated"/创建日期
2. 对明显过时的（如还在说"建设中""规划中"的）做版本标注

**验收：** 无明显过时描述

---

## 执行策略

```
第一优先级：C-1 docstring（无损，快）
第二优先级：C-2 + C-3（测试类，低风险）
第三优先级：C-6 web前端测试 + C-7 CI部署
第四优先级：C-8 竞品监控前端 + C-4 WeApp
第五优先级：C-5 Mixin 重构（需仔细规划拆分步骤）
收尾清理：C-9 agents目录 + C-10 README检查
```

**节奏：** 逐批执行，每批 commit + pytest 验证
