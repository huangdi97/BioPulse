#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# BioPulse · 部署脚本
# 用法: ./scripts/deploy.sh
# 功能: git pull → docker compose build → up → health check
# ============================================================

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "=== [1/5] 拉取最新代码 ==="
git pull

echo "=== [2/5] 构建 Docker 镜像 ==="
docker compose build

echo "=== [3/5] 停止旧容器 ==="
docker compose down

echo "=== [4/5] 启动新容器 ==="
docker compose up -d

echo "=== [5/5] 健康检查 ==="
sleep 5

SERVICES=(
  "cloud:8000"
  "sales-coach:8001"
  "opportunity:8002"
  "assistant:8003"
  "sales-assistant:8004"
  "pharma-intel:8006"
  "management:8012"
)

ALL_PASS=true
for svc in "${SERVICES[@]}"; do
  name="${svc%%:*}"
  port="${svc##*:}"
  status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${port}/health" 2>/dev/null || echo "000")
  if [ "$status" = "200" ]; then
    echo "  ✅ $name (:$port) — $status"
  else
    echo "  ❌ $name (:$port) — $status"
    ALL_PASS=false
  fi
done

if [ "$ALL_PASS" = true ]; then
  echo ""
  echo "✅ 所有服务启动成功！"
  exit 0
else
  echo ""
  echo "⚠️  部分服务未通过健康检查，请检查日志：docker compose logs"
  exit 1
fi
