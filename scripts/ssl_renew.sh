#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# BioPulse · SSL 证书检查与自动续期
# 用法: ./scripts/ssl_renew.sh
# 可加入 cron: 0 6 * * * /opt/biopulse/scripts/ssl_renew.sh
# ============================================================

DOMAIN="biopulse.example.com"
CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"
LOG_FILE="/var/log/ssl_renew.log"
WARN_DAYS=30

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "=== SSL 证书检查开始 ==="

# 检查证书是否存在
if [ ! -f "${CERT_DIR}/fullchain.pem" ]; then
    log "❌ 证书文件不存在: ${CERT_DIR}/fullchain.pem"
    log "请先运行: sudo certbot --nginx -d ${DOMAIN}"
    exit 1
fi

# 获取证书到期时间
expiry_date=$(openssl x509 -enddate -noout -in "${CERT_DIR}/fullchain.pem" 2>/dev/null | cut -d= -f2)
if [ -z "$expiry_date" ]; then
    log "❌ 无法读取证书到期时间"
    exit 1
fi

expiry_epoch=$(date -d "$expiry_date" +%s 2>/dev/null)
current_epoch=$(date +%s)
days_left=$(( (expiry_epoch - current_epoch) / 86400 ))

log "📅 证书到期: $expiry_date (剩余 ${days_left} 天)"

if [ "$days_left" -le 0 ]; then
    log "❌ 证书已过期！立即续期..."
    sudo certbot renew --force-renewal --non-interactive
    sudo nginx -s reload
    log "✅ 证书已续期，Nginx 已重载"
elif [ "$days_left" -le "$WARN_DAYS" ]; then
    log "⚠️  证书将在 ${days_left} 天后到期，执行续期..."
    sudo certbot renew --non-interactive
    if [ $? -eq 0 ]; then
        sudo nginx -s reload
        log "✅ 证书续期成功，Nginx 已重载"
    else
        log "⚠️  certbot renew 返回非零，请手动检查"
    fi
else
    log "✅ 证书有效期充足（${days_left} 天），无需操作"
fi

# 输出当前证书信息
echo ""
sudo certbot certificates 2>/dev/null | tee -a "$LOG_FILE"

log "=== SSL 证书检查结束 ==="
