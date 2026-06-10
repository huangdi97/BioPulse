"""Domain: userprofile"""

USERPROFILE_SQL = """\
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                persona_type TEXT DEFAULT \"\",
                specialization TEXT DEFAULT \"\",
                experience_level TEXT DEFAULT \"mid\",
                preferred_content_types TEXT DEFAULT \"[]\",
                custom_tags TEXT DEFAULT \"[]\",
                embedding TEXT DEFAULT \"\",
                updated_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_up_user ON user_profiles(user_id);

            CREATE TABLE IF NOT EXISTS user_behaviors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                action_type TEXT NOT NULL,
                target_type TEXT DEFAULT \"\",
                target_id TEXT DEFAULT \"\",
                metadata TEXT DEFAULT \"{}\",
                session_id TEXT DEFAULT \"\",
                duration_seconds INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_ub_user ON user_behaviors(user_id);
            CREATE INDEX IF NOT EXISTS idx_ub_action ON user_behaviors(action_type);
            CREATE INDEX IF NOT EXISTS idx_ub_target ON user_behaviors(target_type);

            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                rec_type TEXT NOT NULL,
                rec_target_id TEXT DEFAULT \"\",
                rec_title TEXT DEFAULT \"\",
                rec_reason TEXT DEFAULT \"\",
                score REAL DEFAULT 0.0,
                strategy_name TEXT DEFAULT \"\",
                clicked INTEGER DEFAULT 0,
                dismissed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_rec_user ON recommendations(user_id);
            CREATE INDEX IF NOT EXISTS idx_rec_type ON recommendations(rec_type);
"""
