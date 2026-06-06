"""Domain: exec"""

EXEC_SQL = """\
            CREATE TABLE IF NOT EXISTS agent_execution_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE,
                source TEXT DEFAULT "internal",
                session_id TEXT DEFAULT "",
                agent_role TEXT DEFAULT "",
                action_type TEXT DEFAULT "process",
                input_data TEXT DEFAULT "{}",
                output_data TEXT DEFAULT "{}",
                status TEXT DEFAULT "pending",
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                result_verified INTEGER DEFAULT 0,
                verification_detail TEXT DEFAULT "",
                requires_human_approval INTEGER DEFAULT 0,
                assigned_to TEXT DEFAULT "",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                duration_ms INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_aet_task ON agent_execution_tasks(task_id);
            CREATE INDEX IF NOT EXISTS idx_aet_status ON agent_execution_tasks(status);
            CREATE INDEX IF NOT EXISTS idx_aet_session ON agent_execution_tasks(session_id);

            CREATE TABLE IF NOT EXISTS mcp_tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_name TEXT UNIQUE,
                description TEXT DEFAULT "",
                tool_version TEXT DEFAULT "1.0.0",
                endpoint_url TEXT DEFAULT "",
                input_schema TEXT DEFAULT "{}",
                output_schema TEXT DEFAULT "{}",
                auth_required INTEGER DEFAULT 0,
                enabled INTEGER DEFAULT 1,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_mcp_name ON mcp_tools(tool_name);

            CREATE TABLE IF NOT EXISTS mcp_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_name TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                user_role TEXT DEFAULT "",
                params TEXT DEFAULT "{}",
                result TEXT DEFAULT "{}",
                granted INTEGER DEFAULT 0,
                reason TEXT DEFAULT "",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_mcp_audit_tool ON mcp_audit_log(tool_name);
            CREATE INDEX IF NOT EXISTS idx_mcp_audit_user ON mcp_audit_log(user_id);
            CREATE INDEX IF NOT EXISTS idx_mcp_audit_at ON mcp_audit_log(created_at);

            CREATE TABLE IF NOT EXISTS orchestration_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT UNIQUE,
                description TEXT DEFAULT "",
                steps TEXT DEFAULT "[]",
                version TEXT DEFAULT "1.0.0",
                enabled INTEGER DEFAULT 1,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_ot_name ON orchestration_templates(template_name);
"""
