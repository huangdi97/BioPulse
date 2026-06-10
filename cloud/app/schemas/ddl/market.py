"""Domain: market"""

MARKET_SQL = """\
            CREATE TABLE IF NOT EXISTS market_intel_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                source_type TEXT NOT NULL DEFAULT 'competitor',
                target_keywords TEXT DEFAULT '[]',
                is_active INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_intel_sources_type ON market_intel_sources(source_type);
            CREATE INDEX IF NOT EXISTS idx_intel_sources_active ON market_intel_sources(is_active);
            CREATE TABLE IF NOT EXISTS market_intel_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER REFERENCES market_intel_sources(id),
                title TEXT NOT NULL,
                summary TEXT DEFAULT '',
                content TEXT DEFAULT '',
                url TEXT DEFAULT '',
                item_type TEXT NOT NULL DEFAULT 'competitor',
                relevance_tags TEXT DEFAULT '[]',
                impact_level TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'unread',
                ai_analysis TEXT DEFAULT '',
                collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_intel_items_type ON market_intel_items(item_type);
            CREATE INDEX IF NOT EXISTS idx_intel_items_status ON market_intel_items(status);
            CREATE INDEX IF NOT EXISTS idx_intel_items_impact ON market_intel_items(impact_level);
            CREATE INDEX IF NOT EXISTS idx_intel_items_time ON market_intel_items(collected_at);
"""
