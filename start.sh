#!/usr/bin/env bash
# ============================================================
# 一云四端 · 一键启动脚本（模块化）
# 用法:
#   ./start.sh               默认启动 Cloud(8000) + 管理端前端
#   ./start.sh full          全部5个后端 + 前端
#   ./start.sh cloud         仅 Cloud(8000)
#   ./start.sh coach         Cloud(8000) + Sales-Coach(8001)
#   ./start.sh opportunity   Cloud(8000) + Opportunity(8002)
#   ./start.sh assistant     Cloud(8000) + Assistant(8003)
#   ./start.sh sales         Cloud(8000) + Sales-Assistant(8004)
#   ./start.sh all-frontend  Cloud(8000) + 管理端 + 制药情报Web
#   ./start.sh demo          Cloud + 管理端 + 销售助手 + 种子数据
# ============================================================
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"
MODE="${1:-default}"

PIDS=()
FRONTEND_PIDS=()

# ---------- 工具函数 ----------
cleanup() {
    echo ""
    echo "→ 停止所有服务..."
    for pid in "${FRONTEND_PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null
    echo "  已停止"
    exit 0
}
trap cleanup SIGINT SIGTERM

health_check() {
    local port=$1
    local name=$2
    local max_retries=30
    local retry=0
    echo -n "  [$name] 等待就绪 "
    while [ $retry -lt $max_retries ]; do
        if curl -sf "http://localhost:${port}/health" > /dev/null 2>&1; then
            echo " ✓"
            return 0
        fi
        echo -n "."
        sleep 1
        retry=$((retry + 1))
    done
    echo " ✗ (超时)"
    return 1
}

start_backend() {
    local name=$1
    local port=$2
    local module=$3
    uvicorn "$module" --host 0.0.0.0 --port "$port" --log-level warning &
    local pid=$!
    PIDS+=("$pid")
    echo "  [$name] 启动 → PID $pid"
    health_check "$port" "$name"
}

start_frontend() {
    local dir=$1
    local port=$2
    local name=$3
    if [ ! -d "$dir" ]; then
        echo "  [!] ${name} 目录不存在，跳过"
        return
    fi
    (cd "$dir" && npm run dev -- --port "$port" --host 0.0.0.0) &
    local pid=$!
    FRONTEND_PIDS+=("$pid")
    echo "  [${name}] 启动 → http://localhost:${port} (PID $pid)"
}

# ---------- 前置检查 ----------
echo "→ 检查 .env ..."
if [ ! -f .env ]; then
    echo "  ✗ .env 不存在，请先创建 (cp .env.example .env)"
    exit 1
fi
echo "  ok"

echo "→ 激活 venv ..."
if [ -d venv ]; then
    source venv/bin/activate
elif [ -d .venv ]; then
    source .venv/bin/activate
else
    echo "  ✗ venv 不存在"
    exit 1
fi
echo "  ok"

echo "→ 检查 Python 依赖 ..."
python -c "import fastapi, uvicorn, sqlite3" 2>/dev/null || {
    echo "  ✗ 依赖缺失，请运行 pip install -r requirements.txt"
    exit 1
}
echo "  ok"

# ---------- 数据库初始化 ----------
echo "→ 初始化数据库..."
python -c "
from cloud.app.database import init_db
from cloud.app.agent_database import init_agent_db
from cloud.app.research_database import init_research_db
init_agent_db()
init_db()
init_research_db()
print('  DB init done')
"

# ---------- 服务定义 ----------
CLOUD_SVC="cloud:8000:cloud.app.main:app"
COACH_SVC="sales-coach:8001:sales_coach.app.main:app"
OPPORTUNITY_SVC="opportunity:8002:opportunity.app.main:app"
ASSISTANT_SVC="assistant:8003:assistant.app.main:app"
SALES_SVC="sales-assistant:8004:sales_assistant.app.main:app"
PHARMA_SVC="pharma-intel:8006:pharma_intel.app.main:app"
MGMT_SVC="management:8012:management.app.main:app"

declare -A SVC_MAP
SVC_MAP["cloud"]="$CLOUD_SVC"
SVC_MAP["coach"]="$COACH_SVC"
SVC_MAP["opportunity"]="$OPPORTUNITY_SVC"
SVC_MAP["assistant"]="$ASSISTANT_SVC"
SVC_MAP["sales"]="$SALES_SVC"
SVC_MAP["pharma"]="$PHARMA_SVC"
SVC_MAP["management"]="$MGMT_SVC"

# ---------- 模式映射 ----------
declare -A MODE_MAP
MODE_MAP["default"]="cloud,management"
MODE_MAP["full"]="cloud,coach,opportunity,assistant,sales"
MODE_MAP["cloud"]="cloud"
MODE_MAP["coach"]="cloud,coach"
MODE_MAP["opportunity"]="cloud,opportunity"
MODE_MAP["assistant"]="cloud,assistant"
MODE_MAP["sales"]="cloud,sales"
MODE_MAP["all-frontend"]="cloud,management"
MODE_MAP["demo"]="cloud,management,sales"

NEED_FRONTEND=false
NEED_WEB=false
NEED_SEED=false

case "$MODE" in
    default|all-frontend) NEED_FRONTEND=true ;;
    full)                 NEED_FRONTEND=true ;;
    demo)                 NEED_FRONTEND=true; NEED_SEED=true ;;
esac

case "$MODE" in
    all-frontend) NEED_WEB=true ;;
esac

SERVICES="${MODE_MAP[$MODE]:-cloud}"

# ---------- 启动后端 ----------
echo ""
echo "→ 启动后端服务 (模式: ${MODE})..."

IFS=',' read -ra SVC_LIST <<< "$SERVICES"
for key in "${SVC_LIST[@]}"; do
    entry="${SVC_MAP[$key]}"
    IFS=':' read -r name port module app <<< "$entry"
    start_backend "$name" "$port" "${module}:${app}"
done

# ---------- 种子数据 (demo 模式) ----------
if [ "$NEED_SEED" = true ]; then
    echo ""
    echo "→ 写入种子数据..."
    python cloud/seed_demo.py && echo "  种子数据完成" || echo "  种子数据失败"
fi

# ---------- 前端 ----------
if [ "$NEED_FRONTEND" = true ]; then
    echo ""
    echo "→ 启动前端 (管理端)..."
    start_frontend "frontend" 5173 "管理端"
fi

if [ "$NEED_WEB" = true ]; then
    echo ""
    echo "→ 启动前端 (制药情报)..."
    start_frontend "web" 5174 "制药情报"
fi

# ---------- 打印 URL ----------
echo ""
echo "============================================"
echo "  一云四端 · 服务已启动 (模式: ${MODE})"
echo "  Cloud:          http://localhost:8000"
if [[ "$SERVICES" == *"coach"* ]]; then
    echo "  Sales-Coach:    http://localhost:8001"
fi
if [[ "$SERVICES" == *"opportunity"* ]]; then
    echo "  Opportunity:    http://localhost:8002"
fi
if [[ "$SERVICES" == *"assistant"* ]]; then
    echo "  Assistant:      http://localhost:8003"
fi
if [[ "$SERVICES" == *"sales"* ]]; then
    echo "  Sales-Assistant: http://localhost:8004"
fi
if [ "$NEED_FRONTEND" = true ]; then
    echo "  管理端:         http://localhost:5173"
fi
if [ "$NEED_WEB" = true ]; then
    echo "  制药情报:       http://localhost:5174"
fi
echo "============================================"
echo "  按 Ctrl+C 停止所有服务"
echo ""

wait
