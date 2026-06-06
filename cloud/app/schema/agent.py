"""Domain: agent"""

AGENT_SQL = """\
            CREATE TABLE IF NOT EXISTS agent_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role_type TEXT NOT NULL DEFAULT 'sales_rep',
                description TEXT DEFAULT '',
                system_prompt TEXT NOT NULL,
                input_schema TEXT DEFAULT '{}',
                output_schema TEXT DEFAULT '{}',
                temperature REAL DEFAULT 0.7,
                max_tokens INTEGER DEFAULT 2048,
                allowed_tools TEXT DEFAULT '[]',
                is_active INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_agent_roles_type ON agent_roles(role_type);
            CREATE TABLE IF NOT EXISTS agent_pipelines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS pipeline_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline_id INTEGER NOT NULL REFERENCES agent_pipelines(id),
                step_order INTEGER NOT NULL,
                agent_role_id INTEGER NOT NULL REFERENCES agent_roles(id),
                input_mapping TEXT DEFAULT '{}',
                custom_prompt_override TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_pipeline_steps_order ON pipeline_steps(pipeline_id, step_order);
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline_id INTEGER NOT NULL REFERENCES agent_pipelines(id),
                user_input TEXT DEFAULT '',
                status TEXT DEFAULT 'running',
                result TEXT DEFAULT '{}',
                error TEXT DEFAULT '',
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                created_by INTEGER REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS pipeline_step_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL REFERENCES pipeline_runs(id),
                step_order INTEGER NOT NULL,
                agent_role_id INTEGER NOT NULL,
                agent_role_name TEXT DEFAULT '',
                input_data TEXT DEFAULT '{}',
                output_data TEXT DEFAULT '{}',
                ai_response_raw TEXT DEFAULT '',
                tokens_used INTEGER DEFAULT 0,
                started_at TEXT,
                completed_at TEXT,
                status TEXT DEFAULT 'pending'
            );
            CREATE INDEX IF NOT EXISTS idx_step_runs_run ON pipeline_step_runs(run_id);
"""
