#!/usr/bin/env bash
# PostgreSQL 备份脚本 — 压缩 + 时间戳命名 + 7 天自动清理
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
DB_NAME="${PGDATABASE:-biopulse}"
DB_HOST="${PGHOST:-localhost}"
DB_PORT="${PGPORT:-5432}"
DB_USER="${PGUSER:-postgres}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz"

pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" | gzip > "$FILENAME"

echo "Backup created: $FILENAME"

# 清理超过 RETENTION_DAYS 天的旧备份
find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete
echo "Cleaned up backups older than ${RETENTION_DAYS} days from ${BACKUP_DIR}"