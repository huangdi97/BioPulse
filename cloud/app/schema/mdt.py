"""Domain: mdt"""

MDT_SQL = """\
            CREATE TABLE IF NOT EXISTS mdt_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                question TEXT NOT NULL,
                context TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'active',
                consensus TEXT DEFAULT '',
                consensus_json TEXT DEFAULT '{}',
                round_count INTEGER DEFAULT 0,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_mdt_status ON mdt_sessions(status);
            CREATE TABLE IF NOT EXISTS mdt_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES mdt_sessions(id),
                agent_role_id INTEGER NOT NULL REFERENCES agent_roles(id),
                role_name TEXT DEFAULT '',
                stance TEXT DEFAULT 'neutral',
                vote_weight REAL DEFAULT 1.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_mdt_participant_session ON mdt_participants(session_id);
            CREATE TABLE IF NOT EXISTS mdt_opinions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES mdt_sessions(id),
                participant_id INTEGER NOT NULL REFERENCES mdt_participants(id),
                round_number INTEGER NOT NULL,
                opinion TEXT DEFAULT '',
                summary TEXT DEFAULT '',
                sentiment TEXT DEFAULT 'neutral',
                confidence REAL DEFAULT 0.5,
                key_points TEXT DEFAULT '[]',
                ai_response_raw TEXT DEFAULT '',
                tokens_used INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_mdt_opinions_session ON mdt_opinions(session_id);
            CREATE TABLE IF NOT EXISTS async_mdt_opinions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id INTEGER NOT NULL REFERENCES soap_decisions(id),
                contributor_id INTEGER NOT NULL REFERENCES users(id),
                contributor_role TEXT DEFAULT '',
                opinion TEXT NOT NULL,
                supporting_data TEXT DEFAULT '',
                stance TEXT DEFAULT 'neutral',
                confidence REAL DEFAULT 0.5,
                attachments TEXT DEFAULT '[]',
                is_final INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_async_mdt_decision ON async_mdt_opinions(decision_id);
            CREATE INDEX IF NOT EXISTS idx_async_mdt_contributor ON async_mdt_opinions(contributor_id);
"""
