"""Domain: training"""

TRAINING_SQL = """\
            CREATE TABLE IF NOT EXISTS training_modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'compliance',
                difficulty TEXT NOT NULL DEFAULT 'medium',
                content TEXT DEFAULT '',
                prerequisites TEXT DEFAULT '[]',
                passing_score REAL DEFAULT 0.7,
                estimated_minutes INTEGER DEFAULT 15,
                is_active INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_tm_category ON training_modules(category);
            CREATE INDEX IF NOT EXISTS idx_tm_difficulty ON training_modules(difficulty);
            CREATE TABLE IF NOT EXISTS training_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                module_id INTEGER NOT NULL REFERENCES training_modules(id),
                score REAL DEFAULT 0.0,
                passed INTEGER DEFAULT 0,
                time_spent_seconds INTEGER DEFAULT 0,
                answers TEXT DEFAULT '[]',
                feedback TEXT DEFAULT '',
                difficulty_used TEXT DEFAULT 'medium',
                next_difficulty TEXT DEFAULT '',
                completed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_ts_user ON training_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_ts_module ON training_sessions(module_id);
            CREATE TABLE IF NOT EXISTS training_attributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                training_session_id INTEGER REFERENCES training_sessions(id),
                metric_name TEXT NOT NULL,
                metric_before REAL DEFAULT 0.0,
                metric_after REAL DEFAULT 0.0,
                change_pct REAL DEFAULT 0.0,
                attribution_score REAL DEFAULT 0.0,
                confidence REAL DEFAULT 0.0,
                analysis TEXT DEFAULT '',
                period_days INTEGER DEFAULT 30,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_ta_user ON training_attributions(user_id);
            CREATE INDEX IF NOT EXISTS idx_ta_metric ON training_attributions(metric_name);
            CREATE TABLE IF NOT EXISTS training_scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                script_id TEXT UNIQUE,
                script_name TEXT,
                source_agent_role TEXT,
                source_collaboration_id TEXT,
                description TEXT,
                steps TEXT DEFAULT "[]",
                difficulty TEXT DEFAULT "mid",
                target_roles TEXT DEFAULT "[]",
                score REAL,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_ts_script ON training_scripts(script_id);
            CREATE INDEX IF NOT EXISTS idx_ts_role ON training_scripts(source_agent_role);

            CREATE TABLE IF NOT EXISTS training_roi_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id TEXT UNIQUE,
                period_start TEXT,
                period_end TEXT,
                training_hours REAL,
                participants INTEGER,
                behavior_change_score REAL,
                sales_impact REAL,
                cost_savings REAL,
                roi REAL,
                metadata TEXT DEFAULT "{}",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_tra_id ON training_roi_analysis(analysis_id);
"""
