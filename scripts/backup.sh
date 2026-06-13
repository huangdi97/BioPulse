#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="data/backups/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

for db in data/*.db; do
    [ -f "$db" ] || continue
    cp "$db" "$BACKUP_DIR/"
done

find data/backups -maxdepth 2 -type d -mtime +30 -exec rm -rf {} + 2>/dev/null || true
