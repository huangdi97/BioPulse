"""数据库 SCHEMA SQL 字符串。"""

_BASE_SCHEMA = """
CREATE TABLE IF NOT EXISTS schedule (
    id {pk},
    title TEXT NOT NULL,
    description TEXT,
    event_type TEXT,
    start_time TEXT NOT NULL,
    end_time TEXT,
    location TEXT,
    is_completed INTEGER DEFAULT 0,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS meeting_note (
    id {pk},
    schedule_id INTEGER NOT NULL REFERENCES schedule(id),
    title TEXT NOT NULL,
    content TEXT,
    participants TEXT,
    action_items TEXT,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS content_library (
    id {pk},
    title TEXT NOT NULL,
    content_type TEXT NOT NULL DEFAULT 'product_material',
    category TEXT,
    content TEXT,
    tags TEXT,
    summary TEXT,
    file_reference TEXT,
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS strategy_simulation (
    id {pk},
    hcp_name TEXT,
    visit_date TEXT,
    goal TEXT,
    approach TEXT,
    talking_points TEXT,
    expected_outcome TEXT,
    actual_outcome TEXT,
    reflection TEXT,
    effectiveness INTEGER,
    status TEXT DEFAULT 'planned',
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS hcp (
    id {pk},
    name TEXT NOT NULL,
    hospital TEXT,
    department TEXT,
    specialty TEXT,
    tier TEXT DEFAULT 'C',
    city TEXT,
    phone TEXT,
    email TEXT,
    wechat TEXT,
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS product (
    id {pk},
    name TEXT NOT NULL,
    category TEXT,
    specification TEXT,
    company TEXT,
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS hcp_product_relation (
    id {pk},
    hcp_id INTEGER NOT NULL REFERENCES hcp(id),
    product_id INTEGER NOT NULL REFERENCES product(id),
    relation_type TEXT NOT NULL,
    strength INTEGER DEFAULT 3,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS visit_hcp (
    id {pk},
    schedule_id INTEGER NOT NULL REFERENCES schedule(id),
    hcp_id INTEGER NOT NULL REFERENCES hcp(id),
    products_discussed TEXT,
    hcp_feedback TEXT,
    follow_up_required INTEGER DEFAULT 0,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS coaching_prompt (
    id {pk},
    trigger_type TEXT,
    trigger_keywords TEXT,
    scenario TEXT,
    prompt_template TEXT,
    priority INTEGER DEFAULT 5,
    category TEXT,
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS coaching_session (
    id {pk},
    schedule_id INTEGER,
    hcp_name TEXT,
    current_scenario TEXT,
    status TEXT DEFAULT 'active',
    started_at TEXT,
    ended_at TEXT,
    notes TEXT,
    created_by INTEGER,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS anomaly_rule (
    id {pk},
    rule_name TEXT,
    metric TEXT,
    operator TEXT,
    threshold REAL,
    severity TEXT DEFAULT 'medium',
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS anomaly_alert (
    id {pk},
    rule_id INTEGER NOT NULL REFERENCES anomaly_rule(id),
    entity_type TEXT,
    entity_id INTEGER,
    detected_value REAL,
    severity TEXT,
    message TEXT,
    status TEXT DEFAULT 'open',
    detected_at TEXT,
    resolved_at TEXT,
    resolved_by INTEGER,
    created_at TEXT
);
"""

SCHEMA_SQL = _BASE_SCHEMA.replace("{pk}", "INTEGER PRIMARY KEY AUTOINCREMENT")
PG_SCHEMA_SQL = _BASE_SCHEMA.replace("{pk}", "SERIAL PRIMARY KEY")
