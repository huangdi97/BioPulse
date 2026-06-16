#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="backups/db"
RETENTION_DAYS=30
mkdir -p "$BACKUP_DIR"
FAILED=0

for db in data/*.db; do
    [ -f "$db" ] || continue
    base=$(basename "$db")
    ts=$(date +%Y%m%d_%H%M%S)
    backup_path="$BACKUP_DIR/${base}.${ts}"
    echo "Backing up $db → $backup_path"
    if sqlite3 "$db" ".backup '$backup_path'"; then
        echo "  ✅ $base done"
    else
        echo "  ❌ $base FAILED"
        FAILED=1
    fi
done

echo "Cleaning backups older than ${RETENTION_DAYS} days..."
find "$BACKUP_DIR" -name "*.db.*" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

exit $FAILED
