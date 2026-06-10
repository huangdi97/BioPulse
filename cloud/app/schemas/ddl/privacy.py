"""Domain: privacy"""

PRIVACY_SQL = """\
            CREATE TABLE IF NOT EXISTS privacy_compute_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE,
                compute_type TEXT,
                sensitivity_level TEXT DEFAULT "medium",
                data_summary TEXT DEFAULT "",
                selected_scheme TEXT DEFAULT "",
                status TEXT DEFAULT "pending",
                epsilon_used REAL DEFAULT 0.0,
                noise_level REAL DEFAULT 0.0,
                result_summary TEXT DEFAULT "",
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_pcj_job ON privacy_compute_jobs(job_id);
            CREATE INDEX IF NOT EXISTS idx_pcj_type ON privacy_compute_jobs(compute_type);

            CREATE TABLE IF NOT EXISTS federated_rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                round_id TEXT UNIQUE,
                model_name TEXT,
                round_number INT,
                participant_count INT DEFAULT 0,
                aggregation_method TEXT DEFAULT "fed_avg",
                global_metrics TEXT DEFAULT "{}",
                status TEXT DEFAULT "pending",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_fr_round ON federated_rounds(round_id);
            CREATE INDEX IF NOT EXISTS idx_fr_type ON federated_rounds(model_name);

            CREATE TABLE IF NOT EXISTS nmpa_compliance_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_id TEXT UNIQUE,
                document_type TEXT,
                content_summary TEXT DEFAULT "",
                check_result TEXT DEFAULT "pass",
                violations_found INT DEFAULT 0,
                violation_details TEXT DEFAULT "[]",
                human_review_required INT DEFAULT 0,
                human_reviewer TEXT DEFAULT "",
                human_reviewed_at TEXT,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_ncl_log ON nmpa_compliance_logs(log_id);
            CREATE INDEX IF NOT EXISTS idx_ncl_type ON nmpa_compliance_logs(document_type);
"""
