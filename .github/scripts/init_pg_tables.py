"""CI: 预建所有子项目 PG 数据库表。"""

import importlib
import os
import sys

import psycopg

sys.path.insert(0, os.getcwd())

from shared.conftest_base import convert_schema_to_pg, get_pg_url

# (module_path, schema_attr, test_db, pg_db_name)
SUBPROJECTS = [
    ("cloud.app.database", "SCHEMA_SQL", "data/test_cloud.db"),
    ("opportunity.app.database", "SCHEMA_SQL", "data/test_opportunity.db"),
    ("assistant.app.database", "SCHEMA_SQL", "data/test_assistant.db"),
    ("sales_assistant.app.database", "SCHEMA_SQL", "data/test_sales_assistant.db"),
    ("sales_coach.app.database", "SCHEMA", "data/test_sales_coach.db"),
    ("management.app.database", "SCHEMA", "data/test_management.db"),
]


def main():
    pg_url = os.environ.get("DATABASE_URL", "")
    if not pg_url:
        print("❌ DATABASE_URL not set, skipping PG table init")
        sys.exit(1)

    print(f"📦 DATABASE_URL base: {pg_url.split('@')[0]}@***")

    for mod_path, schema_attr, test_db in SUBPROJECTS:
        db_name = get_pg_url(test_db).rsplit("/", 1)[-1]
        print(f"\n🔧 {mod_path:40} → {db_name}")

        # Import module safely
        try:
            mod = importlib.import_module(mod_path)
        except Exception as e:
            print(f"  ⚠️  import failed: {e}")
            continue

        # Get schema SQL
        schema_sql = getattr(mod, schema_attr, "") or getattr(mod, "SCHEMA_SQL", "") or getattr(mod, "SCHEMA", "")
        if not schema_sql:
            print(f"  ⚠️  no schema SQL found (tried {schema_attr}, SCHEMA_SQL, SCHEMA)")
            continue

        # Convert to PG-compatible SQL
        pg_schema = convert_schema_to_pg(schema_sql)

        # Connect and execute
        full_url = get_pg_url(test_db)
        try:
            conn = psycopg.connect(full_url)
            conn.autocommit = True
            cur = conn.cursor()
            # Create tables
            cur.execute(pg_schema)
            cur.close()
            conn.close()
            print("  ✅ tables created successfully")
        except Exception as e:
            print(f"  ❌ {e}")

    print("\n✅ All done")


if __name__ == "__main__":
    main()
