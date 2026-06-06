"""Domain: route"""

ROUTE_SQL = """\
            CREATE TABLE IF NOT EXISTS route_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                priority INTEGER NOT NULL DEFAULT 100,
                condition_field TEXT NOT NULL DEFAULT 'keyword',
                condition_operator TEXT NOT NULL DEFAULT 'contains',
                condition_value TEXT NOT NULL,
                target_role_id INTEGER REFERENCES agent_roles(id),
                fallback_role_id INTEGER,
                max_tokens INTEGER DEFAULT 2048,
                temperature REAL DEFAULT 0.7,
                is_active INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_route_priority ON route_rules(priority);
            CREATE TABLE IF NOT EXISTS route_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_text TEXT NOT NULL,
                matched_rule_id INTEGER,
                matched_rule_name TEXT DEFAULT '',
                assigned_role_id INTEGER,
                assigned_role_name TEXT DEFAULT '',
                confidence REAL DEFAULT 0.0,
                response_summary TEXT DEFAULT '',
                tokens_used INTEGER DEFAULT 0,
                latency_ms INTEGER DEFAULT 0,
                source TEXT DEFAULT '',
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_route_logs_role ON route_logs(assigned_role_id);
            CREATE INDEX IF NOT EXISTS idx_route_logs_time ON route_logs(created_at);
            CREATE TABLE IF NOT EXISTS route_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_id INTEGER UNIQUE REFERENCES agent_roles(id),
                total_routed INTEGER DEFAULT 0,
                avg_confidence REAL DEFAULT 0.0,
                avg_tokens REAL DEFAULT 0.0,
                avg_latency_ms REAL DEFAULT 0.0,
                last_routed_at TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_route_stats_role ON route_stats(role_id);
"""
