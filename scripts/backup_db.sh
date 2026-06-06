#!/bin/bash
# 一云四端 · SQLite 数据库备份脚本
# 用法: ./scripts/backup_db.sh
# 建议: 每日凌晨 3 点运行（见 backup_schedule.md）

set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="$BASE_DIR/data"
BACKUP_ROOT="$DATA_DIR/backups"
DATE_STAMP=$(date +%Y-%m-%d)
BACKUP_DIR="$BACKUP_ROOT/$DATE_STAMP"
RETENTION_DAYS=30

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份所有 .db 文件
DB_COUNT=0
for db in "$DATA_DIR"/*.db; do
    if [ -f "$db" ]; then
        filename=$(basename "$db")
        cp "$db" "$BACKUP_DIR/$filename"
        echo "  ✔ $filename"
        DB_COUNT=$((DB_COUNT + 1))
    fi
done

if [ "$DB_COUNT" -eq 0 ]; then
    echo "⚠ No .db files found in $DATA_DIR"
    exit 0
fi

echo "✅ Backup complete: $BACKUP_DIR ($DB_COUNT files)"

# 清理超过 RETENTION_DAYS 天的旧备份
OLD_COUNT=0
for old_dir in "$BACKUP_ROOT"/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]; do
    if [ -d "$old_dir" ]; then
        dir_date=$(basename "$old_dir")
        if [[ "$(uname)" == "Darwin" ]]; then
            # macOS date
            dir_seconds=$(date -j -f "%Y-%m-%d" "$dir_date" +%s 2>/dev/null || echo 0)
        else
            # Linux date
            dir_seconds=$(date -d "$dir_date" +%s 2>/dev/null || echo 0)
        fi
        if [ "$dir_seconds" -gt 0 ]; then
            now_seconds=$(date +%s)
            age_days=$(( (now_seconds - dir_seconds) / 86400 ))
            if [ "$age_days" -gt "$RETENTION_DAYS" ]; then
                rm -rf "$old_dir"
                echo "  🗑 Removed old backup: $dir_date ($age_days days old)"
                OLD_COUNT=$((OLD_COUNT + 1))
            fi
        fi
    fi
done

[ "$OLD_COUNT" -gt 0 ] && echo "🗑 Cleaned $OLD_COUNT old backup(s) (retention: $RETENTION_DAYS days)"
echo "📊 Current backups: $(ls -1 "$BACKUP_ROOT" | grep -cE '^[0-9]{4}-[0-9]{2}-[0-9]{2}$') days"
