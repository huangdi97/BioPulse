"""Domain: decision"""

DECISION_SQL = """\
            CREATE TABLE IF NOT EXISTS decision_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                pipeline_run_id INTEGER REFERENCES pipeline_runs(id),
                description TEXT DEFAULT '',
                outcome TEXT DEFAULT '',
                outcome_score REAL DEFAULT 0.0,
                context TEXT DEFAULT '{}',
                tags TEXT DEFAULT '[]',
                is_active INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_dec_cases_outcome ON decision_cases(outcome_score);
            CREATE INDEX IF NOT EXISTS idx_dec_cases_run ON decision_cases(pipeline_run_id);
            CREATE TABLE IF NOT EXISTS causal_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL REFERENCES decision_cases(id),
                analysis_type TEXT NOT NULL DEFAULT 'causal',
                summary TEXT DEFAULT '',
                key_drivers TEXT DEFAULT '[]',
                causal_chain TEXT DEFAULT '[]',
                attribution_scores TEXT DEFAULT '{}',
                recommendations TEXT DEFAULT '[]',
                ai_response_raw TEXT DEFAULT '',
                tokens_used INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_causal_case ON causal_analyses(case_id);
            CREATE TABLE IF NOT EXISTS cross_case_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                insight_type TEXT NOT NULL DEFAULT 'pattern',
                summary TEXT DEFAULT '',
                detail TEXT DEFAULT '',
                evidence TEXT DEFAULT '[]',
                confidence REAL DEFAULT 0.5,
                applicability TEXT DEFAULT 'general',
                source_run_ids TEXT DEFAULT '[]',
                is_active INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_insights_type ON cross_case_insights(insight_type);
            CREATE INDEX IF NOT EXISTS idx_insights_confidence ON cross_case_insights(confidence);
            CREATE TABLE IF NOT EXISTS causal_graphs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                graph_id TEXT UNIQUE,
                decision_id TEXT,
                graph_data TEXT DEFAULT "{}",
                summary TEXT,
                node_count INT,
                edge_count INT,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_cg_graph ON causal_graphs(graph_id);
            CREATE INDEX IF NOT EXISTS idx_cg_decision ON causal_graphs(decision_id);

            CREATE TABLE IF NOT EXISTS counterfactual_scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id TEXT UNIQUE,
                strategy_id TEXT,
                base_description TEXT,
                variable_changes TEXT DEFAULT "[]",
                predicted_outcome TEXT DEFAULT "{}",
                confidence REAL,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_cs_scenario ON counterfactual_scenarios(scenario_id);
"""
