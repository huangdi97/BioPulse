"""Domain: did"""

DID_SQL = """\
            CREATE TABLE IF NOT EXISTS did_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                did TEXT NOT NULL UNIQUE,
                entity_type TEXT DEFAULT "user",
                entity_id INTEGER,
                public_key TEXT DEFAULT "",
                status TEXT DEFAULT "active",
                metadata TEXT DEFAULT "{}",
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_did_did ON did_registry(did);
            CREATE INDEX IF NOT EXISTS idx_did_status ON did_registry(status);
            CREATE TABLE IF NOT EXISTS vc_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vc_id TEXT NOT NULL UNIQUE,
                issuer_did TEXT NOT NULL REFERENCES did_registry(did),
                subject_did TEXT NOT NULL REFERENCES did_registry(did),
                credential_type TEXT NOT NULL,
                claims TEXT DEFAULT "{}",
                issuance_date TEXT DEFAULT CURRENT_TIMESTAMP,
                expiration_date TEXT,
                proof TEXT DEFAULT "",
                status TEXT DEFAULT "active",
                revoked_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_vc_issuer ON vc_credentials(issuer_did);
            CREATE INDEX IF NOT EXISTS idx_vc_subject ON vc_credentials(subject_did);
            CREATE INDEX IF NOT EXISTS idx_vc_type ON vc_credentials(credential_type);
            CREATE TABLE IF NOT EXISTS fed_audit_contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contributor_did TEXT NOT NULL REFERENCES did_registry(did),
                contribution_type TEXT NOT NULL,
                payload_hash TEXT DEFAULT "",
                payload_summary TEXT DEFAULT "",
                weight REAL DEFAULT 1.0,
                verified INTEGER DEFAULT 0,
                verified_by TEXT DEFAULT "",
                audit_chain_hash TEXT DEFAULT "",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_fed_contributor ON fed_audit_contributions(contributor_did);
            CREATE INDEX IF NOT EXISTS idx_fed_type ON fed_audit_contributions(contribution_type);
            CREATE TABLE IF NOT EXISTS privacy_budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                did TEXT NOT NULL REFERENCES did_registry(did),
                epsilon_total REAL DEFAULT 1.0,
                epsilon_spent REAL DEFAULT 0.0,
                epsilon_remaining REAL DEFAULT 1.0,
                query_count INTEGER DEFAULT 0,
                last_query_at TEXT,
                reset_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_pb_did ON privacy_budgets(did);
            CREATE TABLE IF NOT EXISTS data_masking_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL UNIQUE,
                field_pattern TEXT NOT NULL,
                masking_type TEXT NOT NULL,
                masking_config TEXT DEFAULT "{}",
                applies_to TEXT DEFAULT "all",
                enabled INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS dp_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                did TEXT NOT NULL REFERENCES did_registry(did),
                operation_type TEXT NOT NULL,
                epsilon_consumed REAL DEFAULT 0.0,
                data_category TEXT DEFAULT "",
                row_count INTEGER DEFAULT 0,
                noise_level REAL DEFAULT 0.0,
                approved INTEGER DEFAULT 1,
                details TEXT DEFAULT "{}",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_dpal_did ON dp_audit_log(did);
            CREATE INDEX IF NOT EXISTS idx_dpal_type ON dp_audit_log(operation_type);
"""
