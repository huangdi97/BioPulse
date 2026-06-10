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
            CREATE TABLE IF NOT EXISTS agent_runtime_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_key TEXT NOT NULL,
                goal TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                iterations INTEGER DEFAULT 0,
                tool_calls INTEGER DEFAULT 0,
                result TEXT,
                error_message TEXT,
                started_at TEXT,
                completed_at TEXT,
                log_detail TEXT DEFAULT '[]',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                checkpoint_data TEXT DEFAULT NULL,
                trace_id TEXT DEFAULT '',
                cost_data TEXT DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_runtime_logs_agent ON agent_runtime_logs(agent_key);
            CREATE INDEX IF NOT EXISTS idx_runtime_logs_status ON agent_runtime_logs(status);
            CREATE INDEX IF NOT EXISTS idx_runtime_logs_trace ON agent_runtime_logs(trace_id);
            CREATE TABLE IF NOT EXISTS agent_runtime_approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT NOT NULL,
                agent_key TEXT NOT NULL,
                goal TEXT NOT NULL,
                step INTEGER DEFAULT 0,
                tool TEXT NOT NULL,
                params TEXT DEFAULT '{}',
                reasoning TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                responded_at TEXT,
                responded_by TEXT DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_approvals_status ON agent_runtime_approvals(status);
            CREATE INDEX IF NOT EXISTS idx_approvals_trace ON agent_runtime_approvals(trace_id);
            CREATE TABLE IF NOT EXISTS agent_brains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_key TEXT NOT NULL,
                user_id INTEGER DEFAULT 0,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                value_type TEXT DEFAULT 'str',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(agent_key, user_id, key)
            );
            CREATE TABLE IF NOT EXISTS agent_state_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                step_id INTEGER DEFAULT 0,
                plan_json TEXT DEFAULT '[]',
                results_json TEXT DEFAULT '[]',
                context_json TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            );
            CREATE INDEX IF NOT EXISTS idx_state_snapshots_agent ON agent_state_snapshots(agent_id);
            CREATE INDEX IF NOT EXISTS idx_state_snapshots_status ON agent_state_snapshots(status);
            CREATE TABLE IF NOT EXISTS agent_runtime_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT NOT NULL,
                step INTEGER NOT NULL,
                state_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_agent_runtime_snapshots_trace_step ON agent_runtime_snapshots(trace_id, step);
"""
