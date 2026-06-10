"""Domain: memory"""

MEMORY_SQL = """\
            CREATE TABLE IF NOT EXISTS memory_gates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                importance_threshold REAL DEFAULT 0.5,
                ttl_days INTEGER DEFAULT 90,
                retention_policy TEXT DEFAULT 'normal',
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS memory_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT DEFAULT '',
                memory_type TEXT NOT NULL DEFAULT 'insight',
                source_type TEXT DEFAULT '',
                source_id TEXT DEFAULT '',
                importance REAL DEFAULT 0.5,
                context_tags TEXT DEFAULT '[]',
                embedding TEXT DEFAULT '',
                access_count INTEGER DEFAULT 0,
                last_accessed TEXT,
                is_active INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_entries(memory_type);
            CREATE INDEX IF NOT EXISTS idx_memory_importance ON memory_entries(importance);
            CREATE INDEX IF NOT EXISTS idx_memory_accessed ON memory_entries(last_accessed);
            CREATE TABLE IF NOT EXISTS memory_recall_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT DEFAULT '',
                memory_ids TEXT DEFAULT '[]',
                result_count INTEGER DEFAULT 0,
                context TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS memory_utility_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_entry_id INTEGER NOT NULL UNIQUE REFERENCES memory_entries(id),
                utility_score REAL DEFAULT 0.0,
                access_frequency REAL DEFAULT 0.0,
                recency_score REAL DEFAULT 0.0,
                importance_score REAL DEFAULT 0.0,
                connectivity_score REAL DEFAULT 0.0,
                decay_rate REAL DEFAULT 0.0,
                last_utility_update TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_mus_score ON memory_utility_scores(utility_score);
            CREATE INDEX IF NOT EXISTS idx_mus_decay ON memory_utility_scores(decay_rate);
            CREATE TABLE IF NOT EXISTS sleep_consolidation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consolidation_type TEXT NOT NULL,
                source_entry_ids TEXT DEFAULT '[]',
                target_entry_id INTEGER REFERENCES memory_entries(id),
                action_detail TEXT DEFAULT '',
                utility_before REAL DEFAULT 0.0,
                utility_after REAL DEFAULT 0.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS memory_consolidation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consolidation_type TEXT NOT NULL,
                source_table TEXT DEFAULT \"\",
                item_count INTEGER DEFAULT 0,
                items_promoted INTEGER DEFAULT 0,
                items_pruned INTEGER DEFAULT 0,
                items_superseded INTEGER DEFAULT 0,
                duration_ms INTEGER DEFAULT 0,
                status TEXT DEFAULT \"completed\",
                details TEXT DEFAULT \"{}\",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS memory_associations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id_a INTEGER NOT NULL REFERENCES memory_entries(id),
                memory_id_b INTEGER NOT NULL REFERENCES memory_entries(id),
                relation_type TEXT NOT NULL DEFAULT 'related',
                weight REAL DEFAULT 1.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_mema_a ON memory_associations(memory_id_a);
            CREATE INDEX IF NOT EXISTS idx_mema_b ON memory_associations(memory_id_b);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_mema_pair ON memory_associations(
                MIN(memory_id_a, memory_id_b), MAX(memory_id_a, memory_id_b)
            );
"""
