"""Conftest base module."""

import os
import re
import sqlite3

DEFAULT_PG_BASE = "postgresql://hermes:hermes_pg_2026@localhost:15432/"


def _pg_base() -> str:
    url = os.getenv("DATABASE_URL", "")
    if not (url.startswith("postgresql://") or url.startswith("postgres://")):
        return DEFAULT_PG_BASE
    if url.count("/") > 2:
        url = url.rsplit("/", 1)[0] + "/"
    return url


def is_pg() -> bool:
    url = os.getenv("DATABASE_URL", "")
    return bool(url and (url.startswith("postgresql://") or url.startswith("postgres://")))


def get_pg_url(test_db_path: str) -> str:
    name_map = {
        "test_cloud.db": "cloud_db",
        "test_assistant.db": "assistant_db",
        "test_opportunity.db": "opportunity_db",
        "test_sales_assistant.db": "sales_assistant_db",
        "test_sales_coach.db": "sales_coach_db",
        "test_management.db": "management_db",
    }
    basename = os.path.basename(test_db_path)
    db_name = name_map.get(basename, basename.replace(".db", ""))
    return _pg_base() + db_name


def convert_schema_to_pg(schema_sql: str) -> str:
    sql = re.sub(
        r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT",
        "SERIAL PRIMARY KEY",
        schema_sql,
        flags=re.IGNORECASE,
    )
    sql = re.sub(
        r"CREATE\s+VIRTUAL\s+TABLE[^;]*;",
        "",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    sql = re.sub(
        r"CREATE\s+TRIGGER.*?END\s*;",
        "",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    sql = re.sub(
        r"PRAGMA[^;]*;",
        "",
        sql,
        flags=re.IGNORECASE,
    )
    sql = re.sub(
        r'DEFAULT\s+"([^"]*)"',
        r"DEFAULT '\1'",
        sql,
    )
    sql = re.sub(r"\n\s*\n\s*\n", "\n\n", sql)
    return sql


_current_test_db = ""


def setup_test_db(module_db, schema_sql: str, test_db_path: str):
    global _current_test_db
    _current_test_db = test_db_path

    if is_pg():
        import psycopg

        pg_url = get_pg_url(test_db_path)
        conn = psycopg.connect(pg_url)
        cur = conn.cursor()
        pg_schema = convert_schema_to_pg(schema_sql)
        cur.execute(pg_schema)
        conn.commit()
        cur.close()
        conn.close()
        module_db.DB_PATH = test_db_path
        module_db.init_db = lambda: None
        # 让 get_db() 指向 PG，否则模块的 database_url 仍是 SQLite 默认值
        module_db.DATABASE_URL = pg_url
        if hasattr(module_db, "_db") and hasattr(module_db._db, "database_url"):
            module_db._db.database_url = pg_url
    else:
        os.makedirs(os.path.dirname(test_db_path), exist_ok=True)
        conn = sqlite3.connect(test_db_path)
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()
        module_db.DB_PATH = test_db_path
        module_db.init_db = lambda: None


def clean_test_tables(tables: list):
    test_db = _current_test_db
    if is_pg():
        import psycopg

        pg_url = get_pg_url(test_db)
        with psycopg.connect(pg_url) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                for t in tables:
                    try:
                        cur.execute(f'TRUNCATE TABLE "{t}" CASCADE')
                    except Exception:
                        pass
    else:
        with sqlite3.connect(test_db) as conn:
            conn.execute("PRAGMA foreign_keys=OFF")
            for t in tables:
                try:
                    conn.execute(f"DELETE FROM {t}")
                except sqlite3.OperationalError:
                    pass  # 兼容操作：表可能已被删除或无数据
            conn.commit()
