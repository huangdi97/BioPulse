import os
import sqlite3

RESEARCH_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "research.db",
)

_TEST_RESEARCH_DB_PATH = None


def _get_research_db_path() -> str:
    """Return the effective research DB path (test override if set)."""
    return _TEST_RESEARCH_DB_PATH or RESEARCH_DB_PATH


def set_test_research_db_path(path: str):
    """Override research DB path for testing. Call before get_research_db()."""
    global _TEST_RESEARCH_DB_PATH
    _TEST_RESEARCH_DB_PATH = path


def get_research_db() -> sqlite3.Connection:
    db_path = _get_research_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_research_db():
    db_path = _get_research_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")

        conn.execute(
            "CREATE TABLE IF NOT EXISTS research_pi_profiles ("
            "pi_id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name TEXT NOT NULL, "
            "hcp_id INTEGER, "
            "institution TEXT NOT NULL DEFAULT '', "
            "department TEXT NOT NULL DEFAULT '', "
            "title TEXT NOT NULL DEFAULT '', "
            "research_areas TEXT NOT NULL DEFAULT '[]', "
            "total_papers INTEGER NOT NULL DEFAULT 0, "
            "total_grants INTEGER NOT NULL DEFAULT 0, "
            "h_index INTEGER NOT NULL DEFAULT 0, "
            "last_updated TEXT NOT NULL DEFAULT ''"
            ")"
        )

        conn.execute(
            "CREATE TABLE IF NOT EXISTS research_products ("
            "product_id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name TEXT NOT NULL, "
            "category TEXT NOT NULL DEFAULT '', "
            "brand TEXT NOT NULL DEFAULT '', "
            "model TEXT NOT NULL DEFAULT '', "
            "spec TEXT NOT NULL DEFAULT '', "
            "unit_price REAL NOT NULL DEFAULT 0.0, "
            "keywords TEXT NOT NULL DEFAULT '[]', "
            "tech_params TEXT NOT NULL DEFAULT '{}', "
            "cert_status TEXT NOT NULL DEFAULT ''"
            ")"
        )

        conn.execute(
            "CREATE TABLE IF NOT EXISTS research_quotations ("
            "quotation_id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "template_id TEXT NOT NULL, "
            "title TEXT NOT NULL DEFAULT '', "
            "customer_name TEXT NOT NULL DEFAULT '', "
            "items_json TEXT NOT NULL DEFAULT '[]', "
            "total_amount REAL NOT NULL DEFAULT 0.0, "
            "status TEXT NOT NULL DEFAULT 'draft', "
            "created_by TEXT NOT NULL DEFAULT '', "
            "created_at TEXT NOT NULL DEFAULT ''"
            ")"
        )

        conn.execute(
            "CREATE TABLE IF NOT EXISTS research_visits ("
            "visit_id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "pi_id INTEGER NOT NULL, "
            "rep_id INTEGER NOT NULL, "
            "visit_date TEXT NOT NULL, "
            "notes TEXT NOT NULL DEFAULT '', "
            "status TEXT NOT NULL DEFAULT 'planned', "
            "created_at TEXT NOT NULL DEFAULT ''"
            ")"
        )

        conn.execute(
            "CREATE TABLE IF NOT EXISTS research_audit_log ("
            "log_id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "event_type TEXT NOT NULL, "
            "entity_type TEXT NOT NULL, "
            "entity_id INTEGER NOT NULL, "
            "old_value TEXT, "
            "new_value TEXT, "
            "operator TEXT NOT NULL DEFAULT '', "
            "timestamp TEXT NOT NULL DEFAULT ''"
            ")"
        )

        conn.commit()


def log_research_audit(
    event_type: str,
    entity_type: str,
    entity_id: int,
    old_value: str | None = None,
    new_value: str | None = None,
    operator: str = "",
) -> None:
    db = get_research_db()
    try:
        db.execute(
            "INSERT INTO research_audit_log (event_type, entity_type, entity_id, old_value, new_value, operator, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
            (event_type, entity_type, entity_id, old_value, new_value, operator),
        )
        db.commit()
    finally:
        db.close()
