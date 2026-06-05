# Batch 1：方向1+3 并行执行

## B1a：排查 research API 401

### 目标
端到端验证发现 research API 返回 401，需要排查根因并修复。

### 方法
1. 检查 research 端（8006）的 JWT 验证逻辑，确认是否验证了正确的 scope
2. 检查 auth 模块的 token 签发逻辑，确认 research scope 是否正确签发
3. 检查双主线身份隔离中 research 用户的 scope 分配
4. 在 assistant 端（8003）和 research 端（8006）分别打印 token payload 做对比

### 预期输出
- 定位到 401 根因（scope 不匹配 / 签名不一致 / 用户不存在）
- 修复代码
- 重新验证 200 OK

---

## B1b：全局 SQL 注入风险扫描与修复

### 目标
扫描一云四端所有 Python 文件中使用字符串拼接 SQL 的地方，改为参数化查询。

### 方法
1. 全局 grep 搜索 `execute(.*f"`、`execute(.*"` 后跟 `+`、`execute(.*format` 模式
2. 逐个确认是否使用了参数化查询（`?` 占位符）
3. 非参数化的全部改为 `cursor.execute(sql, params)` 形式
4. 特别关注 Cloud 端 449 路由中的 SQLite 操作

### 预期输出
- 扫描结果清单（文件名、行号、SQL模式）
- 修复后的代码文件
- 无字符串拼接 SQL 残留

---

# Batch 2：方向1+3 继续

## B2a：修复 research API 401
从 B1a 定位结果修复。

## B2b：全局异常处理 + 结构化日志 + 请求ID
### 全局异常处理
- 为每个服务的 main.py 注册 FastAPI exception_handler
- 统一返回 500 错误，不暴露内部栈信息
- 确保所有异常可预测、可追溯

### 结构化日志
- 统一日志格式为 JSON（timestamp, service, level, message, request_id, user_id）
- 配置 logging 模块的 JSON Formatter

### 请求ID
- 中间件为每个请求生成唯一 request_id
- 注入日志和响应头

## B2c：端到端再验证
修复后重新跑完整闭环。

---

# Batch 3：方向2+3 并行

## B3a：React 前端联调
- 确认后端 7 服务在线
- 逐个页面接入真实 API 调用（替换 mock）
- 修复前后端不一致（字段名、响应格式）

## B3b：代码分层 — Service 层
- 为 Cloud 端创建 `services/` 目录
- 从路由中抽离业务逻辑
- 路由层只负责请求→参数校验→调用Service→返回响应

---

# Batch 4：方向2+3 继续

## B4a：React 联调继续
- 继续修复联调问题
- 所有页面可正常数据展示

## B4b：代码分层 — Repository 层
- 创建 `repositories/` 目录
- 封装所有数据库操作
- Service 层通过 Repository 访问数据

---

# Batch 5：收尾

## B5a：联调完成验证
- 全流程走通

## B5b：配置集中化 + 命名规范
- Pydantic Settings 管理配置
- 统一 API 响应格式
- 数据库命名规范检查
