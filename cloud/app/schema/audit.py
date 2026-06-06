"""Domain: audit"""

AUDIT_SQL = """\
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id INTEGER,
                detail TEXT DEFAULT '',
                source_end TEXT NOT NULL,
                ip_address TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity_type, entity_id);
            CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_audit_action_time ON audit_logs(action, created_at);
            CREATE TABLE IF NOT EXISTS compliance_audit_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_type TEXT NOT NULL DEFAULT 'text',
                content TEXT NOT NULL,
                source_id TEXT DEFAULT '',
                score REAL DEFAULT 0.0,
                risk_level TEXT NOT NULL DEFAULT 'low',
                passed INTEGER NOT NULL DEFAULT 1,
                violations TEXT DEFAULT '[]',
                ai_analysis TEXT DEFAULT '',
                reviewed_by INTEGER REFERENCES users(id),
                reviewed_at TEXT,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_audit_records_type ON compliance_audit_records(message_type);
            CREATE INDEX IF NOT EXISTS idx_audit_records_risk ON compliance_audit_records(risk_level);
            CREATE INDEX IF NOT EXISTS idx_audit_records_time ON compliance_audit_records(created_at);
            CREATE TABLE IF NOT EXISTS audit_chain_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                action TEXT NOT NULL,
                previous_hash TEXT DEFAULT '',
                current_hash TEXT NOT NULL,
                payload TEXT DEFAULT '{}',
                metadata TEXT DEFAULT '{}',
                source TEXT DEFAULT '',
                created_by INTEGER REFERENCES users(id),
                performed_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_chain_entity ON audit_chain_entries(entity_type, entity_id);
            CREATE INDEX IF NOT EXISTS idx_chain_action ON audit_chain_entries(action);
            CREATE INDEX IF NOT EXISTS idx_chain_time ON audit_chain_entries(performed_at);
            CREATE TABLE IF NOT EXISTS training_corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_record_id INTEGER REFERENCES compliance_audit_records(id),
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                category TEXT DEFAULT 'general',
                severity TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'pending',
                assigned_to INTEGER REFERENCES users(id),
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_corrections_audit ON training_corrections(audit_record_id);
            CREATE INDEX IF NOT EXISTS idx_corrections_status ON training_corrections(status);
            CREATE INDEX IF NOT EXISTS idx_corrections_severity ON training_corrections(severity);
"""
