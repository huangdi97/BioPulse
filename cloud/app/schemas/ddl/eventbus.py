"""Domain: eventbus"""

EVENTBUS_SQL = """\
            CREATE TABLE IF NOT EXISTS event_bus_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL UNIQUE,
                display_name TEXT DEFAULT \"\",
                description TEXT DEFAULT \"\",
                source_end TEXT DEFAULT \"cloud\",
                target_ends TEXT DEFAULT \"[]\",
                schema_template TEXT DEFAULT \"{}\",
                priority INTEGER DEFAULT 100,
                enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_ebd_type ON event_bus_definitions(event_type);
            CREATE INDEX IF NOT EXISTS idx_ebd_source ON event_bus_definitions(source_end);

            CREATE TABLE IF NOT EXISTS event_bus_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL UNIQUE,
                event_type TEXT NOT NULL REFERENCES event_bus_definitions(event_type),
                source_end TEXT DEFAULT \"cloud\",
                source_entity_type TEXT DEFAULT \"\",
                source_entity_id TEXT DEFAULT \"\",
                payload TEXT DEFAULT \"{}\",
                correlation_id TEXT DEFAULT \"\",
                priority INTEGER DEFAULT 100,
                status TEXT DEFAULT \"pending\",
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                delivered_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_ebm_type ON event_bus_messages(event_type);
            CREATE INDEX IF NOT EXISTS idx_ebm_status ON event_bus_messages(status);
            CREATE INDEX IF NOT EXISTS idx_ebm_corr ON event_bus_messages(correlation_id);

            CREATE TABLE IF NOT EXISTS event_delivery_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL REFERENCES event_bus_messages(message_id),
                target_end TEXT NOT NULL,
                delivery_status TEXT DEFAULT \"pending\",
                attempt INTEGER DEFAULT 1,
                response_summary TEXT DEFAULT \"\",
                duration_ms INTEGER DEFAULT 0,
                error_message TEXT DEFAULT \"\",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_edl_msg ON event_delivery_log(message_id);
            CREATE INDEX IF NOT EXISTS idx_edl_target ON event_delivery_log(target_end);
"""
