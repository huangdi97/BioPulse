#!/usr/bin/env bash
set -euo pipefail

echo "=== BioPulse 启动脚本 ==="

# 检查依赖
command -v python3 >/dev/null 2>&1 || { echo "需要安装 Python 3"; exit 1; }
PYTHON=$(command -v python3)

echo "[1/4] 检查 Python 依赖..."
if [ ! -f "cloud/requirements.txt" ]; then
    echo "cloud/requirements.txt 不存在，请确认在项目根目录运行此脚本"
    exit 1
fi
$PYTHON -c "import pip" 2>/dev/null || { echo "pip 未安装"; exit 1; }
$PYTHON -m pip install -q -r cloud/requirements.txt

echo "[2/4] 检查环境配置..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo ".env 已从 .env.example 创建，请编辑 .env 填入 API Key"
    else
        echo ".env 文件缺失"
        exit 1
    fi
fi

echo "[3/4] 初始化数据库..."
$PYTHON -c "from cloud.app.database import init_db; init_db()" 2>/dev/null && echo "数据库就绪" || echo "数据库初始化跳过（可能已存在）"

echo "[4/4] 启动开发服务器..."
exec uvicorn cloud.app.main:app --reload --host 0.0.0.0 --port 8000
