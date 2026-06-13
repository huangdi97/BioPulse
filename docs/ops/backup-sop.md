# Database Backup SOP

## Overview
Daily backup of all SQLite databases under `data/*.db`.

## Script
`scripts/backup.sh`

## Schedule (crontab)
```
0 3 * * * /path/to/scripts/backup.sh
```

## What It Does
1. Creates `data/backups/YYYYMMDD/`
2. Copies all `data/*.db` files into that directory
3. Removes backup directories older than 30 days

## Restoration
```bash
cp data/backups/20260614/cloud.db data/cloud.db
```

## Retention
- 30 daily backups retained
- Older backups are automatically pruned
