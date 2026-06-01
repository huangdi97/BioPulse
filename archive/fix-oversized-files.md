# 修复超300行文件 — 执行文档

## 任务总目标
将 Cloud 端4个超300行文件降至300行以内，符合项目编码规范。

---

## 文件清单与方案

### 1. compliance_v2_router.py（当前302行 → ≤300行）
**策略：微调压缩**，零功能改动
- 删除文件末尾多余空行（line 302）
- 合并1组连续空行（2个→1个）
- 预估结果：300行以内

### 2. route_router.py（当前343行 → ≤300行）
**策略：空白行压缩 + 签名压缩**
- 当前33个空行，保留标准间隔（函数间1空行），压缩多余空行 → 省 ~15行
- 压缩长函数签名（多行参数合并为单行或紧凑）→ 省 ~10行
- 调整 select/where 子句里不必要的换行 → 省 ~18行
- 预估结果：290-300行

### 3. memory_utility_router.py（当前351行 → ≤300行）
**策略：空白行压缩 + 签名压缩 + 紧凑格式化**
- 压缩多余空行 → 省 ~10行
- 压缩多行函数签名 → 省 ~5行
- 压缩 SQL 字符串换行（多行SQL合并为紧凑格式）→ 省 ~25行
- 压缩 `_calc_utility` 返回值字典格式 → 省 ~5行
- 压缩 `sleep_consolidate` 里不必要的多行拆分 → 省 ~10行
- 预估结果：290-300行

### 4. database.py（当前1,313行 → ~100行）
**策略：将SQL提取到独立schema.py**
- 创建 `schema.py`：包含所有87张表的 CREATE TABLE SQL，导出为 `SCHEMA_SQL` 常量
- 修改 `database.py`：引入 `from cloud.app.schema import SCHEMA_SQL`，`init_db()` 执行 `conn.executescript(SCHEMA_SQL)`
- 保留 `DB_PATH`、`get_db()`、`init_db()`、和所有 seed 调用
- 删除 conn.row_factory 重复设置（已在 get_db() 中统一处理）
- 新增文件 `schema.py` 不超300行（目标：合适长度，不额外拆分）

---

## 验证清单
- [ ] 4个文件全部 ≤300行
- [ ] `python3 -c "from cloud.app.database import get_db, init_db"` 无导入错误
- [ ] `python3 -c "from cloud.app.memory_utility_router import router"` 无导入错误
- [ ] `python3 -c "from cloud.app.route_router import router"` 无导入错误
- [ ] `python3 -c "from cloud.app.compliance_v2_router import router"` 无导入错误
- [ ] 所有 API 端点可正确路由（路径未变）

---

## 回滚方案
若任一文件导入失败，执行：
```bash
git checkout -- cloud/app/database.py cloud/app/schema.py cloud/app/memory_utility_router.py cloud/app/route_router.py cloud/app/compliance_v2_router.py
```
然后报告错误原因。
