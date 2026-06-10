"""Domain: kg"""

KG_SQL = """\
            CREATE TABLE IF NOT EXISTS kg_entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT NOT NULL UNIQUE,
                entity_type TEXT NOT NULL,
                name TEXT NOT NULL,
                aliases TEXT DEFAULT \"[]\",
                properties TEXT DEFAULT \"{}\",
                source_table TEXT DEFAULT \"\",
                source_row_id INTEGER,
                status TEXT DEFAULT \"active\",
                confidence REAL DEFAULT 1.0,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_kge_type ON kg_entities(entity_type);
            CREATE INDEX IF NOT EXISTS idx_kge_name ON kg_entities(name);

            CREATE TABLE IF NOT EXISTS kg_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_entity_id TEXT NOT NULL REFERENCES kg_entities(entity_id),
                target_entity_id TEXT NOT NULL REFERENCES kg_entities(entity_id),
                relation_type TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                properties TEXT DEFAULT \"{}\",
                direction TEXT DEFAULT \"directed\",
                confidence REAL DEFAULT 1.0,
                source TEXT DEFAULT \"manual\",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_kgr_source ON kg_relations(source_entity_id);
            CREATE INDEX IF NOT EXISTS idx_kgr_target ON kg_relations(target_entity_id);
            CREATE INDEX IF NOT EXISTS idx_kgr_type ON kg_relations(relation_type);

            CREATE TABLE IF NOT EXISTS kg_search_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_hash TEXT NOT NULL,
                query_text TEXT NOT NULL,
                result_summary TEXT DEFAULT \"\",
                result_count INTEGER DEFAULT 0,
                cache_ttl INTEGER DEFAULT 300,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_kgq_hash ON kg_search_cache(query_hash);
"""
