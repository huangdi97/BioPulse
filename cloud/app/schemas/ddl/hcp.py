"""Domain: hcp"""

HCP_SQL = """\
            CREATE TABLE IF NOT EXISTS hcp_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                title TEXT DEFAULT '',
                hospital TEXT DEFAULT '',
                department TEXT DEFAULT '',
                specialty TEXT DEFAULT '',
                city TEXT DEFAULT '',
                tier TEXT DEFAULT 'B',
                traits TEXT DEFAULT '{}',
                prescription_volume REAL DEFAULT 0,
                influence_score REAL DEFAULT 0.5,
                digital_engagement REAL DEFAULT 0.5,
                is_active INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_hcp_tier ON hcp_profiles(tier);
            CREATE INDEX IF NOT EXISTS idx_hcp_specialty ON hcp_profiles(specialty);
            CREATE TABLE IF NOT EXISTS hcp_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hcp_id INTEGER NOT NULL REFERENCES hcp_profiles(id),
                interaction_type TEXT NOT NULL,
                content TEXT DEFAULT '',
                response TEXT DEFAULT '',
                outcome TEXT DEFAULT '',
                strategy_used TEXT DEFAULT '',
                conducted_by INTEGER REFERENCES users(id),
                conducted_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_hcp_int_hcp ON hcp_interactions(hcp_id);
            CREATE INDEX IF NOT EXISTS idx_hcp_int_time ON hcp_interactions(conducted_at);
            CREATE TABLE IF NOT EXISTS hcp_simulations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hcp_id INTEGER NOT NULL REFERENCES hcp_profiles(id),
                scenario TEXT NOT NULL,
                strategy TEXT DEFAULT '',
                expected_outcome TEXT DEFAULT '',
                confidence REAL DEFAULT 0.5,
                suggested_approach TEXT DEFAULT '',
                key_concerns TEXT DEFAULT '',
                recommended_topics TEXT DEFAULT '',
                risk_factors TEXT DEFAULT '',
                simulation_data TEXT DEFAULT '{}',
                status TEXT DEFAULT 'completed',
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_hcp_sim_hcp ON hcp_simulations(hcp_id);
"""
