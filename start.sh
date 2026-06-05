#!/usr/bin/env bash
# ============================================================
# 一云四端 · 一键启动
# 启动所有服务（cloud + 4端 + pharma_intel + management）
# ============================================================
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

# 激活虚拟环境
if [ -d venv ]; then
    source venv/bin/activate
elif [ -d .venv ]; then
    source .venv/bin/activate
fi

# 初始化数据库
echo "→ 初始化数据库..."
python -c "
from cloud.app.database import init_db
from cloud.app.agent_database import init_agent_db
from cloud.app.research_database import init_research_db
init_agent_db()
init_db()
init_research_db()
echo '  DB init done'
"

# 服务定义: (名称, 端口, 模块路径)
SERVICES=(
    "cloud:8000:cloud.app.main:app"
    "opportunity:8002:opportunity.app.main:app"
    "sales-coach:8001:sales_coach.app.main:app"
    "assistant:8003:assistant.app.main:app"
    "sales-assistant:8004:sales_assistant.app.main:app"
    "pharma-intel:8006:pharma_intel.app.main:app"
    "management:8012:management.app.main:app"
)

PIDS=()

cleanup() {
    echo ""
    echo "→ 停止所有服务..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null
    echo "  已停止"
    exit 0
}
trap cleanup SIGINT SIGTERM

echo ""
echo "→ 启动服务..."

for svc in "${SERVICES[@]}"; do
    IFS=':' read -r name port module app <<< "$svc"
    uvicorn "$module" --host 0.0.0.0 --port "$port" &
    PIDS+=($!)
    echo "  [$name] → http://localhost:$port (PID $!)"
done

echo ""
echo "============================================"
echo "  一云四端 · 全部启动"
echo "  Cloud:          http://localhost:8000"
echo "  Opportunity:    http://localhost:8002"
echo "  Sales-Coach:    http://localhost:8001"
echo "  Assistant:      http://localhost:8003"
echo "  Sales-Assistant: http://localhost:8004"
echo "  Pharma-Intel:   http://localhost:8006"
echo "  Management:     http://localhost:8012"
echo "============================================"
echo "  按 Ctrl+C 停止所有服务"
echo ""

# 等待任意子进程退出
wait
