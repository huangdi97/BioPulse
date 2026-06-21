#!/bin/bash
# BioPulse 数据备份脚本
# 备份 SQLite 数据库文件，保留最近7天，自动清理过期

set -euo pipefail

BACKUP_DIR="$(dirname "$0")/archives"
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

mkdir -p "$BACKUP_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] BioPulse 数据备份开始"

# 备份 SQLite 数据库文件
for db in cloud.db research.db data/remediation.db; do
  DB_PATH="$PROJECT_DIR/$db"
  if [ -f "$DB_PATH" ]; then
    # 完整性检查
    INTEGRITY=$(sqlite3 "$DB_PATH" ".integrity_check" 2>&1)
    if [ "$INTEGRITY" != "ok" ]; then
      echo "[WARN] $db 完整性检查失败: $INTEGRITY"
    fi

    # 备份
    BACKUP_FILE="$BACKUP_DIR/$(basename "$db" .db)_$TIMESTAMP.db"
    cp "$DB_PATH" "$BACKUP_FILE"
    # 压缩
    gzip -f "$BACKUP_FILE"
    echo "[OK] $db → $(basename "$BACKUP_FILE").gz ($(du -h "$BACKUP_FILE.gz" | cut -f1))"
  else
    echo "[SKIP] $db 不存在"
  fi
done

# 清理过期备份
find "$BACKUP_DIR" -name "*.gz" -mtime +$RETENTION_DAYS -delete
echo "[OK] 清理 $RETENTION_DAYS 天前的旧备份"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] BioPulse 数据备份完成"
