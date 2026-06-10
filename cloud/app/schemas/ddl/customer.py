"""Domain: customer"""

CUSTOMER_SQL = """\
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                title TEXT DEFAULT '',
                hospital TEXT DEFAULT '',
                department TEXT DEFAULT '',
                specialty TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                email TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                status TEXT DEFAULT 'active',
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);
            CREATE INDEX IF NOT EXISTS idx_customers_hospital ON customers(hospital);
            CREATE TABLE IF NOT EXISTS customer_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                type TEXT NOT NULL DEFAULT 'visit',
                summary TEXT DEFAULT '',
                outcome TEXT DEFAULT '',
                conducted_by INTEGER,
                conducted_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_interactions_customer ON customer_interactions(customer_id);
            CREATE INDEX IF NOT EXISTS idx_interactions_time ON customer_interactions(conducted_at);
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                stage TEXT NOT NULL DEFAULT 'lead',
                probability INTEGER DEFAULT 0,
                estimated_value REAL DEFAULT 0.0,
                actual_value REAL DEFAULT 0.0,
                assigned_to INTEGER REFERENCES users(id),
                close_date TEXT,
                notes TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_opps_customer ON opportunities(customer_id);
            CREATE INDEX IF NOT EXISTS idx_opps_stage ON opportunities(stage);
            CREATE INDEX IF NOT EXISTS idx_opps_assigned ON opportunities(assigned_to);
"""
