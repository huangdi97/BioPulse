"""Domain: collab"""

COLLAB_SQL = """\
            CREATE TABLE IF NOT EXISTS agent_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT NOT NULL,
                agent_role TEXT NOT NULL,
                description TEXT DEFAULT \"\",
                entity_types TEXT DEFAULT \"[]\",
                capabilities TEXT DEFAULT \"[]\",
                confidence REAL DEFAULT 0.5,
                priority INTEGER DEFAULT 100,
                enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_ask_role ON agent_skills(agent_role);
            CREATE INDEX IF NOT EXISTS idx_ask_entity ON agent_skills(entity_types);
            CREATE TABLE IF NOT EXISTS collaboration_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL UNIQUE,
                task_description TEXT DEFAULT \"\",
                source_entity_id TEXT,
                source_agent_role TEXT DEFAULT \"\",
                orchestrator_agent TEXT DEFAULT \"\",
                status TEXT DEFAULT \"active\",
                involved_agents TEXT DEFAULT \"[]\",
                routing_strategy TEXT DEFAULT \"semantic\",
                total_steps INTEGER DEFAULT 0,
                completed_steps INTEGER DEFAULT 0,
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                result_summary TEXT DEFAULT \"\"
            );
            CREATE INDEX IF NOT EXISTS idx_cs_session ON collaboration_sessions(session_id);
            CREATE INDEX IF NOT EXISTS idx_cs_status ON collaboration_sessions(status);
            CREATE TABLE IF NOT EXISTS collaboration_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES collaboration_sessions(session_id),
                step_order INTEGER NOT NULL,
                agent_role TEXT NOT NULL,
                action_type TEXT DEFAULT \"process\",
                input_summary TEXT DEFAULT \"\",
                output_summary TEXT DEFAULT \"\",
                entity_id TEXT,
                status TEXT DEFAULT \"pending\",
                started_at TEXT,
                completed_at TEXT,
                duration_seconds INTEGER DEFAULT 0,
                metadata TEXT DEFAULT \"{}\"
            );
            CREATE INDEX IF NOT EXISTS idx_cstep_session ON collaboration_steps(session_id);
"""
