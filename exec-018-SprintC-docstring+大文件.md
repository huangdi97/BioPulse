# Exec-018 · Sprint C · docstring补全 + 大文件拆分

## 目标
1. 补全四端 service 层的函数 docstring（当前 0-6% → 85%+）
2. 拆分 36 个 >250 行的大文件（重点 300+ 行的）

## 编码准则（完整18条）
1. Think Before Coding 2. Simplicity First 3. Surgical Changes 4. Goal-Driven Execution 5. 架构优先拒绝补丁 6. 面向组件构建 7. 显式优于隐式 8. 代码整洁自文档化 9. 单一职责 10. 组合优于委托 11. 单一状态源 12. 避免语法糖 13. 命名一致性 14. 文件不超过300行 15. 低耦合(模块间只传ID) 16. 必须用opencode写代码 17. 启动规则(write→TG→confirm→opencode) 18. 完整准则写入每个tasks.md不可省略

---

## Batch C1: 补四端 service 层 docstring

### 现状
| 端 | 函数级 docstring | 需要补的文件 |
|:---|:---:|:---|
| assistant | 5.8% | services/ 下 ~10个文件 |
| opportunity | 0% | services/ 下 ~9个文件 |
| sales-assistant | 0% | services/ 下 ~11个文件 |
| sales-coach | 24.7% | services/ 下 ~11个文件 |
| management | 0% | services/ 下 ~4个文件 |

### 操作
对上述端 `services/` 下的所有 Python 文件：
- 给每个 public 函数/方法补充中文 docstring
- 格式：`"""功能描述。Args: 参数说明; Returns: 返回值说明"""`
- 不修改任何逻辑代码
- 不补 test 文件

### 验收标准
- 四端 service 层函数级 docstring 覆盖率 ≥ 80%
- 所有修改通过 ruff 检查

---

## Batch C2: 大文件拆分（优先 >300 行的）

### 现状
36 个 >250 行的文件，其中 22 个 >280 行（接近 300 红线）。先拆 300+ 的：

| 文件 | 行数 | 拆分方案 |
|:---|:---:|:---|
| cloud/app/tests/test_cloud.py | 1681 | 按测试类拆为多个 test_*.py |
| cloud/app/agent_runtime/runtime_core.py | 431 | 已拆过一次但 294→431（需二次分拆） |
| cloud/app/tests/test_mdt.py | 405 | 按测试类拆分 |
| cloud/app/tests/test_agents.py | 399 | 按测试类拆分 |
| pharma_intel/app/seed_data.py | 355 | 按领域拆为多个 seed_*.py |
| compliance_v2_report.py | 337 | 提取报表模板到独立文件 |
| sage_engine_service.py | 327 | 提取辅助函数到独立模块 |
| memory_writer.py | 322 | 提取记忆格式化到独立文件 |
| bidding_agent_service.py | 310 | 提取 API 调用到独立模块 |
| memory_repository.py | 306 | 提取查询方法到独立文件 |
| cloud/app/main.py | 304 | 提取中间件/事件处理到独立文件 |

### 验收标准
- 所有拆分后文件 ≤ 300 行
- 全部 import 链正常
- 测试通过

---

## 执行顺序

| 顺序 | Batch | 预估耗时 |
|:---|:---|:---:|
| 1 | C1: 四端 service docstring | 20 min |
| 2 | C2: 大文件拆分（分批）| 40 min |
