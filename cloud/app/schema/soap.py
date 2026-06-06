"""Domain: soap"""

SOAP_SQL = """\
            CREATE TABLE IF NOT EXISTS soap_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'general',
                description TEXT DEFAULT '',
                structure TEXT NOT NULL DEFAULT '{}',
                is_active INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS soap_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                template_id INTEGER REFERENCES soap_templates(id),
                subjective TEXT DEFAULT '',
                objective TEXT DEFAULT '',
                assessment TEXT DEFAULT '',
                plan TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'draft',
                priority TEXT DEFAULT 'medium',
                tags TEXT DEFAULT '[]',
                decision_summary TEXT DEFAULT '',
                decided_by INTEGER REFERENCES users(id),
                decided_at TEXT,
                is_active INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_soap_status ON soap_decisions(status);
            CREATE INDEX IF NOT EXISTS idx_soap_priority ON soap_decisions(priority);
"""
