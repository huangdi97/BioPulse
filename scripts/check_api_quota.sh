#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# BioPulse · API/Key 额度监控
# 检查 DeepSeek API 和 SenSen Nova API 剩余额度
# 用法: bash scripts/check_api_quota.sh
# 可加入 cron: 0 9 * * * /opt/biopulse/scripts/check_api_quota.sh
# ============================================================

LOG_FILE="${LOG_FILE:-/var/log/api_quota.log}"
WEBHOOK_URL="${TELEGRAM_WEBHOOK_URL:-}"
WARN_THRESHOLD_USD="${WARN_THRESHOLD_USD:-5}"
CRIT_THRESHOLD_USD="${CRIT_THRESHOLD_USD:-1}"
WARN_THRESHOLD_CALLS="${WARN_THRESHOLD_CALLS:-1000}"
CRIT_THRESHOLD_CALLS="${CRIT_THRESHOLD_CALLS:-100}"

DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-}"
SENSEN_API_KEY="${SENSEN_API_KEY:-}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

send_alert() {
    local level="$1"
    local message="$2"
    log "${level}: ${message}"
    if [ -n "$WEBHOOK_URL" ]; then
        local payload
        payload=$(cat <<EOF
{
    "text": "[API额度${level}] ${message}",
    "priority": "${level}"
}
EOF
)
        curl -s -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "$payload" > /dev/null 2>&1 || log "⚠️  Webhook 发送失败"
    fi
}

log "=== API/Key 额度检查开始 ==="

# --- DeepSeek API ---
if [ -n "$DEEPSEEK_API_KEY" ]; then
    log "🔍 检查 DeepSeek API 额度..."
    DEEPSEEK_RESP=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer ${DEEPSEEK_API_KEY}" \
        "https://api.deepseek.com/user/balance" 2>/dev/null || true)
    HTTP_CODE=$(echo "$DEEPSEEK_RESP" | tail -1)
    BODY=$(echo "$DEEPSEEK_RESP" | sed '$d')

    if [ "$HTTP_CODE" = "200" ] && [ -n "$BODY" ]; then
        BALANCE=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('balance', 0))" 2>/dev/null || echo "unknown")
        log "💰 DeepSeek 余额: \$${BALANCE}"
        if [ "$BALANCE" != "unknown" ]; then
            BALANCE_NUM=$(echo "$BALANCE" | awk '{print int($1)}')
            if [ "$BALANCE_NUM" -le "$CRIT_THRESHOLD_USD" ] 2>/dev/null; then
                send_alert "❌ CRITICAL" "DeepSeek API 余额仅剩 \$${BALANCE}，低于阈值 \$${CRIT_THRESHOLD_USD}，请立即充值！"
            elif [ "$BALANCE_NUM" -le "$WARN_THRESHOLD_USD" ] 2>/dev/null; then
                send_alert "⚠️ WARNING" "DeepSeek API 余额 \$${BALANCE}，低于预警阈值 \$${WARN_THRESHOLD_USD}"
            fi
        fi
    else
        log "⚠️  DeepSeek API 查询失败 (HTTP ${HTTP_CODE})"
    fi
else
    log "ℹ️  DEEPSEEK_API_KEY 未设置，跳过 DeepSeek 额度检查"
fi

# --- SenSen Nova API ---
if [ -n "$SENSEN_API_KEY" ]; then
    log "🔍 检查 SenSen Nova API 额度..."
    SENSEN_RESP=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer ${SENSEN_API_KEY}" \
        -H "Content-Type: application/json" \
        "https://openapi.sensenova.cn/v1/quotas" 2>/dev/null || true)
    HTTP_CODE=$(echo "$SENSEN_RESP" | tail -1)
    BODY=$(echo "$SENSEN_RESP" | sed '$d')

    if [ "$HTTP_CODE" = "200" ] && [ -n "$BODY" ]; then
        REMAINING=$(echo "$BODY" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    calls = data.get('remaining_calls', data.get('quota', {}).get('remaining', 0))
    print(calls)
except Exception:
    print('unknown')
" 2>/dev/null || echo "unknown")
        log "💰 SenSen Nova 剩余调用次数: ${REMAINING}"
        if [ "$REMAINING" != "unknown" ]; then
            REMAIN_NUM=$(echo "$REMAINING" | awk '{print int($1)}')
            if [ "$REMAIN_NUM" -le "$CRIT_THRESHOLD_CALLS" ] 2>/dev/null; then
                send_alert "❌ CRITICAL" "SenSen Nova API 剩余调用 ${REMAINING} 次，低于阈值 ${CRIT_THRESHOLD_CALLS} 次！"
            elif [ "$REMAIN_NUM" -le "$WARN_THRESHOLD_CALLS" ] 2>/dev/null; then
                send_alert "⚠️ WARNING" "SenSen Nova API 剩余调用 ${REMAINING} 次，低于预警阈值 ${WARN_THRESHOLD_CALLS} 次"
            fi
        fi
    else
        log "⚠️  SenSen Nova API 查询失败 (HTTP ${HTTP_CODE})"
    fi
else
    log "ℹ️  SENSEN_API_KEY 未设置，跳过 SenSen Nova 额度检查"
fi

log "=== API/Key 额度检查结束 ==="
