创建一键启动脚本 scripts/start-all.sh，管理全部5个微服务。

## 脚本位置
/home/hermes/one-cloud-four-ends/scripts/start-all.sh

## 端口映射
Cloud → 8008 (cloud.app.main:app)
Assistant → 8003 (assistant.app.main:app)
Opportunity → 8002 (opportunity.app.main:app)
Sales-Assistant → 8004 (sales_assistant.app.main:app) [注意：目录 sales-assistant，包名 sales_assistant]
Sales-Coach → 8001 (sales_coach.app.main:app) [注意：目录 sales-coach，包名 sales_coach]

## 用法
bash scripts/start-all.sh         # 启动全部
bash scripts/start-all.sh status  # 查看状态
bash scripts/start-all.sh stop    # 停止全部
bash scripts/start-all.sh restart # 重启全部

## 实现要求
1. 工作目录：项目根目录 /home/hermes/one-cloud-four-ends/
2. Python：/home/hermes/one-cloud-four-ends/venv/bin/python
3. 日志目录：logs/{service}.log (先 mkdir -p logs)
4. PID文件：logs/{service}.pid
5. 启动命令：nohup $PYTHON -m uvicorn {module}:app --host 0.0.0.0 --port {port} > logs/{service}.log 2>&1 &
6. 启动后 sleep 1 秒，做 curl localhost:{port}/health 检查
7. Cloud 已在运行则跳过（检测端口占用）
8. stop 时读取 pid 文件 kill，status 时检查 pid 是否存活
9. 服务切换标题用 echo 打印醒目提示

## 执行后验证
bash scripts/start-all.sh status  应显示5个服务均 running
bash scripts/start-all.sh stop    应全停
bash scripts/start-all.sh         应全起

# 编码准则（18条完整版）
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
14. 文件不超过300行
15. 低耦合（模块间只传ID）
16. 必须用OpenCode写代码
17. 启动规则：write → TG → confirm → opencode
18. 完整准则写入每个tasks.md不可省略
