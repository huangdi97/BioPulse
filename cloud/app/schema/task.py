"""Domain: task"""

TASK_SQL = """\
            CREATE TABLE IF NOT EXISTS task_boards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                owner_id INTEGER NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS board_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                board_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'todo',
                priority TEXT DEFAULT 'medium',
                assignee_id INTEGER,
                due_date TEXT,
                sort_order INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_board_tasks_board ON board_tasks(board_id, status);
            CREATE INDEX IF NOT EXISTS idx_board_tasks_assignee ON board_tasks(assignee_id);
"""
