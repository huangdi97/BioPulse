"""Domain: workingmem"""

WORKINGMEM_SQL = """\
            CREATE TABLE IF NOT EXISTS working_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                slot_key TEXT NOT NULL,
                slot_value TEXT DEFAULT '',
                slot_type TEXT DEFAULT 'string',
                ttl_seconds INTEGER DEFAULT 1800,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                UNIQUE(session_id, slot_key)
            );
            CREATE INDEX IF NOT EXISTS idx_wm_session ON working_memory(session_id);
            CREATE INDEX IF NOT EXISTS idx_wm_expires ON working_memory(expires_at);
            CREATE TABLE IF NOT EXISTS episodic_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                context TEXT DEFAULT '{}',
                outcome TEXT DEFAULT '',
                valence REAL DEFAULT 0.0,
                intensity REAL DEFAULT 0.5,
                involved_agents TEXT DEFAULT '[]',
                related_entity_type TEXT DEFAULT '',
                related_entity_id INTEGER,
                is_consolidated INTEGER DEFAULT 0,
                created_by TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_em_event ON episodic_memory(event_type);
            CREATE INDEX IF NOT EXISTS idx_em_outcome ON episodic_memory(outcome);
            CREATE INDEX IF NOT EXISTS idx_em_time ON episodic_memory(created_at);
"""
