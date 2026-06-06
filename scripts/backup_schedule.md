# 数据库备份 · 定时任务配置

## 手动运行

```bash
cd /path/to/one-cloud-four-ends
bash scripts/backup_db.sh
```

输出示例：
```
  ✔ cloud.db
  ✔ assistant.db
  ✔ opportunity.db
  ✔ sales_assistant.db
  ✔ sales_coach.db
  ✔ research.db
✅ Backup complete: data/backups/2026-05-29 (6 files)
🗑 Cleaned 3 old backup(s) (retention: 30 days)
📊 Current backups: 5 days
```

## 定时自动备份（crontab）

每天凌晨 3:00 自动执行：

```bash
# 编辑 crontab
crontab -e

# 添加以下行（将路径替换为实际路径）：
0 3 * * * cd /home/hermes/one-cloud-four-ends && bash scripts/backup_db.sh >> data/backups/backup.log 2>&1
```

## 说明

- 备份保存在 `data/backups/YYYY-MM-DD/` 目录下
- 自动保留最近 30 天的备份，更旧的自动删除
- 日志追加到 `data/backups/backup.log`（如需关闭将 `>>` 改为 `&>` ）
- 不设 cron 也不会影响系统运行——备份只是防止 SQLite 文件意外丢失
