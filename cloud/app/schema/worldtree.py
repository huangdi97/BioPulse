"""Domain: worldtree"""

WORLDTREE_SQL = """\
            CREATE TABLE IF NOT EXISTS world_tree_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                parent_id INTEGER REFERENCES world_tree_nodes(id),
                path TEXT DEFAULT '',
                level INTEGER DEFAULT 0,
                node_type TEXT DEFAULT 'tag',
                sort_order INTEGER DEFAULT 0,
                metadata TEXT DEFAULT '{}',
                is_active INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_tree_parent ON world_tree_nodes(parent_id);
            CREATE INDEX IF NOT EXISTS idx_tree_path ON world_tree_nodes(path);
            CREATE INDEX IF NOT EXISTS idx_tree_type ON world_tree_nodes(node_type);
            CREATE TABLE IF NOT EXISTS node_memory_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id INTEGER NOT NULL REFERENCES world_tree_nodes(id),
                memory_entry_id INTEGER NOT NULL REFERENCES memory_entries(id),
                relevance_score REAL DEFAULT 0.5,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(node_id, memory_entry_id)
            );
            CREATE INDEX IF NOT EXISTS idx_nml_node ON node_memory_links(node_id);
            CREATE INDEX IF NOT EXISTS idx_nml_memory ON node_memory_links(memory_entry_id);
            CREATE TABLE IF NOT EXISTS world_tree_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id INTEGER NOT NULL REFERENCES world_tree_nodes(id),
                snapshot_type TEXT DEFAULT 'full',
                subtree_json TEXT DEFAULT '{}',
                memory_count INTEGER DEFAULT 0,
                version INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_snapshot_node ON world_tree_snapshots(node_id);
"""
