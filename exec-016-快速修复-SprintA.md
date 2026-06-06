# Exec-016 · 快速修复（Sprint A）

## 目标
修复审计发现的 3 类高优先级问题：端口号错误、异常吞没、文档过时。

## 编码准则（完整18条）
1. Think Before Coding 2. Simplicity First 3. Surgical Changes 4. Goal-Driven Execution 5. 架构优先拒绝补丁 6. 面向组件构建 7. 显式优于隐式 8. 代码整洁自文档化 9. 单一职责 10. 组合优于委托 11. 单一状态源 12. 避免语法糖 13. 命名一致性 14. 文件不超过300行 15. 低耦合(模块间只传ID) 16. 必须用opencode写代码 17. 启动规则(write→TG→confirm→opencode) 18. 完整准则写入每个tasks.md不可省略

---

## Batch A1: 修复 README.md 端口号

### 现状
README.md 中端口有 3 处错误：

| 服务 | 文档值 | 实际值 |
|:---|:---:|:---:|
| Assistant | 8001 | 8003 |
| Sales-Assistant | 8003 | 8004 |
| Sales-Coach | 8004 | 8001 |

### 修正方案
在 README.md 中找到并替换这三处端口号：
- `Assistant → 8001` → `Assistant → 8003`
- `Sales-Assistant → 8003` → `Sales-Assistant → 8004`
- `Sales-Coach → 8004` → `Sales-Coach → 8001`

### 验收标准
- grep 确认三处端口全部改为正确值
- 各端 main.py 中的端口（8000/8001/8003/8004）与文档一致

---

## Batch A2: 修复 ARCHITECTURE.md 错误

### 2a: ADR 描述错误

| 位置 | 当前描述 | 正确描述 |
|:---|:---|:---|
| ADR-0004 | "拆分后全量测试" | "Agent 通信平面抽象" |
| ADR-0005 | "Mixin 命名区隔" | "项目线严格分离" |

### 2b: 删除已不存在文件的引用
搜索 `reflector.py` 和 `unified_memory_service.py` 在 ARCHITECTURE.md 中的引用，删除或替换为当前实际存在的文件。

### 验收标准
- `grep "拆分后全量测试" ARCHITECTURE.md` 无匹配
- `grep "Mixin 命名区隔" ARCHITECTURE.md` 无匹配
- `grep "reflector.py" ARCHITECTURE.md` 无匹配（或不指向已删除文件）
- `grep "unified_memory_service" ARCHITECTURE.md` 无匹配

---

## Batch A3: 修复 5 处 except:pass

### 3a: `opportunity/app/bidding_agent_router.py:192`
**问题：** 定时扫描任务 `run_bidding_scan` 中 `except Exception: pass`
**修复：** 改为 `logger.exception(...)` 并继续执行（不中断任务调度）

### 3b: `opportunity/app/services/bidding_agent_service.py:92`
**问题：** 通知发送失败时 `except Exception: pass`
**修复：** 改为 `logger.exception(...)` 并记录失败但不阻塞

### 3c: `cloud/app/database.py:183,187`
**问题：** ALTER TABLE 和 CREATE INDEX 异常被静默吞掉
**修复：** 保留 silence 但加 `logger.debug(...)` 日志。如果已有日志则改为 `logger.warning(...)`

### 3d: `cloud/app/agent_runtime/runtime_core.py`
**问题：** `_save_snapshot` 中用 `except Exception: pass`
**修复：** 改为 `logger.error(...)`，不影响正常流程

**注意：** 每个 except:pass 处确认是否已有 logger，没有则引入 `import logging; logger = logging.getLogger(__name__)`

### 验收标准
- `grep "except.*:.*pass" -r opportunity/` 除 test 外不应有 `except: pass`
- `grep "except Exception: pass" -r cloud/app/database.py` 不应匹配
- `grep "except Exception: pass" -r cloud/app/agent_runtime/` 不应匹配

---

## Batch A4: 统一 43 处硬编码 `localhost:8000`

### 方案
1. 在 `shared/config.py` 或 `shared/app_settings.py` 中添加 `AI_GATEWAY_URL` 配置项，默认 `http://localhost:8000`
2. 搜索所有硬编码 `http://localhost:8000` 的文件，改为 `settings.AI_GATEWAY_URL` 导入
3. 主要修 `runtime_core.py` 的 `_raw_llm_call` 方法

### 文件清单
需要修改的 34 个文件（先修核心文件，分批进行）。先处理最关键的：
- `cloud/app/agent_runtime/runtime_core.py` — `_raw_llm_call` 中的硬编码
- `cloud/app/services/*.py` — 直接调用 localhost:8000/ai/chat 的 service

### 验收标准
- `grep "localhost:8000" cloud/app/` 除 test 外不应有匹配
- 所有端仍能通过 `shared.config.Settings.AI_GATEWAY_URL` 调用 AI

---

## 执行顺序

| 顺序 | Batch | 依赖 | 预估耗时 |
|:---|:---|:---|:---:|
| 1 | A1: README 端口修复 | 无 | 5 min |
| 2 | A2: ARCHITECTURE.md 修复 | 无 | 5 min |
| 3 | A3: 5处 except:pass 修复 | 无 | 10 min |
| 4 | A4: 硬编码 URL 统一 | 无 | 20 min |
| — | 全量测试验证 | 各 Batch 无冲突 | 15 min |
