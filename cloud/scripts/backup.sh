#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/backup_config.sh"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME=$(basename "$DB_PATH")
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME%.*}_${TIMESTAMP}.db"

mkdir -p "$BACKUP_DIR"

python3 -c "
import sqlite3
src = sqlite3.connect('$DB_PATH')
dst = sqlite3.connect('$BACKUP_FILE')
src.backup(dst)
dst.close()
src.close()
"

gzip "$BACKUP_FILE"

find "$BACKUP_DIR" -name "${DB_NAME%.*}_*.db.gz" -mtime +"$RETENTION_DAYS" -delete