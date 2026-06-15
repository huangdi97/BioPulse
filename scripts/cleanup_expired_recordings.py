"""
清理超过 2 年的加密录音文件。

用法：
    python scripts/cleanup_expired_recordings.py

行为：
    - 扫描 visit_drafts 表中 expires_at 早于当前时间的行
    - 删除对应的音频文件
    - 标记录音状态为 'expired'
"""

import os
import sqlite3
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cloud.app.database import DB_PATH


def cleanup_expired_recordings(dry_run: bool = False) -> int:
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    expired = conn.execute(
        "SELECT id, audio_file_path FROM visit_drafts WHERE expires_at IS NOT NULL AND expires_at < ? AND status != 'expired'",
        (now,),
    ).fetchall()
    count = 0
    for row in expired:
        if row["audio_file_path"] and os.path.exists(row["audio_file_path"]):
            if not dry_run:
                os.remove(row["audio_file_path"])
            count += 1
        if not dry_run:
            conn.execute("UPDATE visit_drafts SET status = 'expired' WHERE id = ?", (row["id"],))
    conn.commit()
    conn.close()
    return count


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    removed = cleanup_expired_recordings(dry_run=dry)
    print(f"{'[DRY-RUN] ' if dry else ''}Cleaned up {removed} expired recording(s)")
