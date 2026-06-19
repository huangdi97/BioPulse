#!/bin/bash
# BioPulse 备份配置
DB_PATH="${DB_PATH:-data/biopulse.db}"
BACKUP_DIR="${BACKUP_DIR:-cloud/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
