#!/usr/bin/env bash
# BioPulse 数据库备份脚本
# 备份 SQLite 数据库文件到 backups/ 目录，保留最近 7 天
set -euo pipefail

BACKUP_DIR="backups"
DATA_DIR="data"
RETENTION_DAYS=7
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$BACKUP_DIR"

for db_file in "$DATA_DIR"/*.db; do
    [ -f "$db_file" ] || continue
    base_name=$(basename "$db_file")
    backup_path="$BACKUP_DIR/${base_name%.db}_${TIMESTAMP}.db"
    cp "$db_file" "$backup_path"
    echo "Backed up: $db_file -> $backup_path"
done

# Cleanup old backups (older than RETENTION_DAYS)
find "$BACKUP_DIR" -name "*.db" -type f -mtime +$RETENTION_DAYS -delete
echo "Cleaned up backups older than $RETENTION_DAYS days."

echo "Backup complete: $(date)"