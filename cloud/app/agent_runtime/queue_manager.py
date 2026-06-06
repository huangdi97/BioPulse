"""Agent 任务队列管理模块，支持入队、出队、完成/失败及恢复。"""

from datetime import datetime


class AgentQueueManager:
    """基于 SQLite 的 Agent 任务队列管理器。"""

    def __init__(self, db):
        self._db = db
        self._init_table()

    def _init_table(self):
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS agent_task_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_key TEXT NOT NULL,
                goal TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                scheduled_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                result TEXT,
                error TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        self._db.commit()

    def enqueue(self, agent_key: str, goal: str, scheduled_at: str) -> int:
        cur = self._db.execute(
            "INSERT INTO agent_task_queue (agent_key, goal, scheduled_at) VALUES (?, ?, ?)",
            (agent_key, goal, scheduled_at),
        )
        self._db.commit()
        return cur.lastrowid

    def dequeue(self) -> dict | None:
        cur = self._db.execute(
            "SELECT * FROM agent_task_queue WHERE status='pending' AND scheduled_at <= datetime('now') ORDER BY scheduled_at LIMIT 1"
        )
        row = cur.fetchone()
        if row is None:
            return None
        task = dict(row)
        self._db.execute(
            "UPDATE agent_task_queue SET status='running', started_at=datetime('now') WHERE id=?",
            (task["id"],),
        )
        self._db.commit()
        task["status"] = "running"
        task["started_at"] = datetime.now().isoformat()
        return task

    def complete(self, task_id: int, result: str) -> None:
        self._db.execute(
            "UPDATE agent_task_queue SET status='completed', completed_at=datetime('now'), result=? WHERE id=?",
            (result, task_id),
        )
        self._db.commit()

    def fail(self, task_id: int, error: str) -> None:
        self._db.execute(
            "UPDATE agent_task_queue SET status='failed', completed_at=datetime('now'), error=? WHERE id=?",
            (error, task_id),
        )
        self._db.commit()

    def list_pending(self) -> list[dict]:
        cur = self._db.execute("SELECT * FROM agent_task_queue WHERE status='pending' ORDER BY scheduled_at")
        return [dict(r) for r in cur.fetchall()]

    def list_by_agent(self, agent_key: str, limit: int = 20) -> list[dict]:
        cur = self._db.execute(
            "SELECT * FROM agent_task_queue WHERE agent_key=? ORDER BY id DESC LIMIT ?",
            (agent_key, limit),
        )
        return [dict(r) for r in cur.fetchall()]

    def recover(self) -> None:
        self._db.execute("UPDATE agent_task_queue SET status='pending', started_at=NULL WHERE status='running'")
        self._db.commit()
