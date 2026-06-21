#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# BioPulse · 性能测试一键运行脚本
# 依赖: k6 (https://k6.io/docs/getting-started/installation/)
# 用法: ./deploy/benchmark/run.sh [smoke|load|stress|all]
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/results"
K6_SCRIPTS="${SCRIPT_DIR}/k6-scripts"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BASE_URL="${BASE_URL:-http://localhost:8000}"

mkdir -p "$RESULTS_DIR"

print_header() {
    echo ""
    echo "=========================================="
    echo " BioPulse · $1"
    echo " 时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo " 目标: $BASE_URL"
    echo "=========================================="
}

run_test() {
    local name="$1"
    local script="$2"
    local output_file="${RESULTS_DIR}/${name}_${TIMESTAMP}.json"

    print_header "运行 ${name} 测试"

    if [ ! -f "$script" ]; then
        echo "❌ 脚本不存在: $script"
        return 1
    fi

    echo "📝 结果输出: $output_file"
    echo ""

    K6_STATSD_ENABLE=false \
    k6 run "$script" \
        -e BASE_URL="$BASE_URL" \
        --out json="$output_file" \
        --summary-export="${RESULTS_DIR}/${name}_${TIMESTAMP}_summary.json"

    echo ""
    echo "✅ ${name} 测试完成"
    echo "   原始数据: ${output_file}"
    echo "   汇总数据: ${RESULTS_DIR}/${name}_${TIMESTAMP}_summary.json"
}

print_system_info() {
    echo "--- 系统信息 ---"
    echo "CPU: $(nproc) 核"
    if command -v free &>/dev/null; then
        echo "内存: $(free -h | awk '/Mem:/{print $2}') 总 / $(free -h | awk '/Mem:/{print $7}') 可用"
    fi
    if command -v uptime &>/dev/null; then
        echo "负载: $(uptime | awk -F'load average:' '{print $2}')"
    fi
    echo ""
}

# ---------- 主逻辑 ----------
MODE="${1:-all}"

echo ""
echo "██████╗ ██╗ ██████╗ ██████╗ ██╗   ██╗██╗     ███████╗███████╗"
echo "██╔══██╗██║██╔═══██╗██╔══██╗██║   ██║██║     ██╔════╝██╔════╝"
echo "██████╔╝██║██║   ██║██████╔╝██║   ██║██║     █████╗  ███████╗"
echo "██╔══██╗██║██║   ██║██╔═══╝ ██║   ██║██║     ██╔══╝  ╚════██║"
echo "██████╔╝██║╚██████╔╝██║     ╚██████╔╝███████╗███████╗███████║"
echo "╚═════╝ ╚═╝ ╚═════╝ ╚═╝      ╚═════╝ ╚══════╝╚══════╝╚══════╝"
echo ""
echo " BioPulse · 性能基准测试套件"
echo " 模式: ${MODE}"
echo " 时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

print_system_info

case "$MODE" in
    smoke)
        run_test "smoke" "${K6_SCRIPTS}/smoke.js"
        ;;
    load)
        run_test "load" "${K6_SCRIPTS}/load.js"
        ;;
    stress)
        run_test "stress" "${K6_SCRIPTS}/stress.js"
        ;;
    all)
        run_test "smoke" "${K6_SCRIPTS}/smoke.js"
        echo ""
        echo "--- 等待 10 秒后开始负载测试 ---"
        sleep 10
        run_test "load" "${K6_SCRIPTS}/load.js"
        echo ""
        echo "--- 等待 10 秒后开始压力测试 ---"
        sleep 10
        run_test "stress" "${K6_SCRIPTS}/stress.js"
        ;;
    *)
        echo "用法: $0 [smoke|load|stress|all]"
        echo "   smoke  冒烟测试 (1 VU, 30s)"
        echo "   load   负载测试 (10→50 VU, 3min)"
        echo "   stress 压力测试 (10→100 VU, 5min)"
        echo "   all    依次运行全部测试 (默认)"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo " 🎯 全部测试完成！"
echo " 结果目录: $RESULTS_DIR"
echo "=========================================="
ls -lh "$RESULTS_DIR"/*"${TIMESTAMP}"* 2>/dev/null || echo " (无结果文件)"
