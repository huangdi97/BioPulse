"""Domain: misc"""

MISC_SQL = """\
            CREATE TABLE IF NOT EXISTS effect_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_id TEXT UNIQUE,
                agent_role TEXT,
                metric_type TEXT,
                metric_value REAL,
                metric_unit TEXT,
                source_table TEXT,
                source_row_id TEXT,
                source_sub TEXT DEFAULT '',
                period_start TEXT,
                period_end TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_em_agent ON effect_metrics(agent_role);
            CREATE INDEX IF NOT EXISTS idx_em_source_sub ON effect_metrics(source_sub);

            CREATE TABLE IF NOT EXISTS benchmark_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT UNIQUE,
                report_name TEXT,
                report_type TEXT,
                data_source TEXT DEFAULT "aggregated",
                summary TEXT,
                metrics TEXT DEFAULT "{}",
                period TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_br_report ON benchmark_reports(report_id);

            CREATE TABLE IF NOT EXISTS agent_marketplace (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT UNIQUE,
                item_name TEXT,
                item_type TEXT DEFAULT "template",
                description TEXT,
                agent_config TEXT DEFAULT "{}",
                category TEXT,
                price_model TEXT DEFAULT "free",
                rating REAL,
                download_count INTEGER,
                enabled INTEGER,
                publisher TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_am_item ON agent_marketplace(item_id);
            CREATE INDEX IF NOT EXISTS idx_am_cat ON agent_marketplace(category);

            CREATE TABLE IF NOT EXISTS supply_chain_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT UNIQUE,
                item_name TEXT,
                sku TEXT,
                category TEXT,
                current_stock INTEGER,
                min_stock INTEGER,
                max_stock INTEGER,
                unit_price REAL,
                supplier TEXT,
                status TEXT DEFAULT "active",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_sci_item ON supply_chain_items(item_id);

            CREATE TABLE IF NOT EXISTS sensor_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
                session_name TEXT,
                event_type TEXT DEFAULT "academic_meeting",
                location TEXT,
                start_time TEXT,
                end_time TEXT,
                data_summary TEXT DEFAULT "{}",
                status TEXT DEFAULT "active",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_ss_session ON sensor_sessions(session_id);

            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL DEFAULT "",
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS token_budget (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                model TEXT NOT NULL,
                daily_used INTEGER NOT NULL DEFAULT 0,
                alert_sent INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_token_budget_user ON token_budget(user_id, model);

            CREATE TABLE IF NOT EXISTS token_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                model TEXT NOT NULL,
                tokens INTEGER NOT NULL DEFAULT 0,
                cost REAL NOT NULL DEFAULT 0.0,
                usage_date TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_token_usage_user ON token_usage(user_id, model, usage_date);
"""
