SCHEMA_SQL = """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                role TEXT DEFAULT "user",
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS api_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                token_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS compliance_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                keyword TEXT NOT NULL,
                max_value REAL,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS contents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                category TEXT NOT NULL,
                tags TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'draft',
                compliance_score REAL,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_by INTEGER,
                created_at TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS user_team (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                team_id INTEGER NOT NULL REFERENCES teams(id),
                role TEXT DEFAULT 'member',
                created_at TEXT,
                UNIQUE(user_id, team_id)
            );
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id INTEGER,
                detail TEXT DEFAULT '',
                source_end TEXT NOT NULL,
                ip_address TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity_type, entity_id);
            CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_audit_action_time ON audit_logs(action, created_at);
            CREATE TABLE IF NOT EXISTS notification_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                title_template TEXT NOT NULL,
                body_template TEXT NOT NULL,
                category TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                template_id INTEGER,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                category TEXT NOT NULL,
                ref_type TEXT DEFAULT '',
                ref_id INTEGER,
                context_json TEXT DEFAULT '',
                is_read INTEGER DEFAULT 0,
                read_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_notif_user ON notifications(user_id, is_read);
            CREATE INDEX IF NOT EXISTS idx_notif_user_time ON notifications(user_id, created_at);
            CREATE TABLE IF NOT EXISTS task_boards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                owner_id INTEGER NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS board_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                board_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'todo',
                priority TEXT DEFAULT 'medium',
                assignee_id INTEGER,
                due_date TEXT,
                sort_order INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_board_tasks_board ON board_tasks(board_id, status);
            CREATE INDEX IF NOT EXISTS idx_board_tasks_assignee ON board_tasks(assignee_id);
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                title TEXT DEFAULT '',
                hospital TEXT DEFAULT '',
                department TEXT DEFAULT '',
                specialty TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                email TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                status TEXT DEFAULT 'active',
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);
            CREATE INDEX IF NOT EXISTS idx_customers_hospital ON customers(hospital);
            CREATE TABLE IF NOT EXISTS customer_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                type TEXT NOT NULL DEFAULT 'visit',
                summary TEXT DEFAULT '',
                outcome TEXT DEFAULT '',
                conducted_by INTEGER,
                conducted_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_interactions_customer ON customer_interactions(customer_id);
            CREATE INDEX IF NOT EXISTS idx_interactions_time ON customer_interactions(conducted_at);
            CREATE TABLE IF NOT EXISTS system_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                description TEXT DEFAULT '',
                updated_by INTEGER,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                stage TEXT NOT NULL DEFAULT 'lead',
                probability INTEGER DEFAULT 0,
                estimated_value REAL DEFAULT 0.0,
                actual_value REAL DEFAULT 0.0,
                assigned_to INTEGER REFERENCES users(id),
                close_date TEXT,
                notes TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_opps_customer ON opportunities(customer_id);
            CREATE INDEX IF NOT EXISTS idx_opps_stage ON opportunities(stage);
            CREATE INDEX IF NOT EXISTS idx_opps_assigned ON opportunities(assigned_to);
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
            CREATE TABLE IF NOT EXISTS agent_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role_type TEXT NOT NULL DEFAULT 'sales_rep',
                description TEXT DEFAULT '',
                system_prompt TEXT NOT NULL,
                input_schema TEXT DEFAULT '{}',
                output_schema TEXT DEFAULT '{}',
                temperature REAL DEFAULT 0.7,
                max_tokens INTEGER DEFAULT 2048,
                allowed_tools TEXT DEFAULT '[]',
                is_active INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_agent_roles_type ON agent_roles(role_type);
            CREATE TABLE IF NOT EXISTS agent_pipelines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS pipeline_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline_id INTEGER NOT NULL REFERENCES agent_pipelines(id),
                step_order INTEGER NOT NULL,
                agent_role_id INTEGER NOT NULL REFERENCES agent_roles(id),
                input_mapping TEXT DEFAULT '{}',
                custom_prompt_override TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_pipeline_steps_order ON pipeline_steps(pipeline_id, step_order);
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline_id INTEGER NOT NULL REFERENCES agent_pipelines(id),
                user_input TEXT DEFAULT '',
                status TEXT DEFAULT 'running',
                result TEXT DEFAULT '{}',
                error TEXT DEFAULT '',
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                created_by INTEGER REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS pipeline_step_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL REFERENCES pipeline_runs(id),
                step_order INTEGER NOT NULL,
                agent_role_id INTEGER NOT NULL,
                agent_role_name TEXT DEFAULT '',
                input_data TEXT DEFAULT '{}',
                output_data TEXT DEFAULT '{}',
                ai_response_raw TEXT DEFAULT '',
                tokens_used INTEGER DEFAULT 0,
                started_at TEXT,
                completed_at TEXT,
                status TEXT DEFAULT 'pending'
            );
            CREATE INDEX IF NOT EXISTS idx_step_runs_run ON pipeline_step_runs(run_id);
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
            CREATE TABLE IF NOT EXISTS compliance_audit_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_type TEXT NOT NULL DEFAULT 'text',
                content TEXT NOT NULL,
                source_id TEXT DEFAULT '',
                score REAL DEFAULT 0.0,
                risk_level TEXT NOT NULL DEFAULT 'low',
                passed INTEGER NOT NULL DEFAULT 1,
                violations TEXT DEFAULT '[]',
                ai_analysis TEXT DEFAULT '',
                reviewed_by INTEGER REFERENCES users(id),
                reviewed_at TEXT,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_audit_records_type ON compliance_audit_records(message_type);
            CREATE INDEX IF NOT EXISTS idx_audit_records_risk ON compliance_audit_records(risk_level);
            CREATE INDEX IF NOT EXISTS idx_audit_records_time ON compliance_audit_records(created_at);
            CREATE TABLE IF NOT EXISTS audit_chain_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                action TEXT NOT NULL,
                previous_hash TEXT DEFAULT '',
                current_hash TEXT NOT NULL,
                payload TEXT DEFAULT '{}',
                metadata TEXT DEFAULT '{}',
                source TEXT DEFAULT '',
                created_by INTEGER REFERENCES users(id),
                performed_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_chain_entity ON audit_chain_entries(entity_type, entity_id);
            CREATE INDEX IF NOT EXISTS idx_chain_action ON audit_chain_entries(action);
            CREATE INDEX IF NOT EXISTS idx_chain_time ON audit_chain_entries(performed_at);
            CREATE TABLE IF NOT EXISTS training_corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_record_id INTEGER REFERENCES compliance_audit_records(id),
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                category TEXT DEFAULT 'general',
                severity TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'pending',
                assigned_to INTEGER REFERENCES users(id),
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_corrections_audit ON training_corrections(audit_record_id);
            CREATE INDEX IF NOT EXISTS idx_corrections_status ON training_corrections(status);
            CREATE INDEX IF NOT EXISTS idx_corrections_severity ON training_corrections(severity);
            CREATE TABLE IF NOT EXISTS mdt_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                question TEXT NOT NULL,
                context TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'active',
                consensus TEXT DEFAULT '',
                consensus_json TEXT DEFAULT '{}',
                round_count INTEGER DEFAULT 0,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_mdt_status ON mdt_sessions(status);
            CREATE TABLE IF NOT EXISTS mdt_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES mdt_sessions(id),
                agent_role_id INTEGER NOT NULL REFERENCES agent_roles(id),
                role_name TEXT DEFAULT '',
                stance TEXT DEFAULT 'neutral',
                vote_weight REAL DEFAULT 1.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_mdt_participant_session ON mdt_participants(session_id);
            CREATE TABLE IF NOT EXISTS mdt_opinions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES mdt_sessions(id),
                participant_id INTEGER NOT NULL REFERENCES mdt_participants(id),
                round_number INTEGER NOT NULL,
                opinion TEXT DEFAULT '',
                summary TEXT DEFAULT '',
                sentiment TEXT DEFAULT 'neutral',
                confidence REAL DEFAULT 0.5,
                key_points TEXT DEFAULT '[]',
                ai_response_raw TEXT DEFAULT '',
                tokens_used INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_mdt_opinions_session ON mdt_opinions(session_id);
            CREATE TABLE IF NOT EXISTS memory_gates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                importance_threshold REAL DEFAULT 0.5,
                ttl_days INTEGER DEFAULT 90,
                retention_policy TEXT DEFAULT 'normal',
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS memory_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT DEFAULT '',
                memory_type TEXT NOT NULL DEFAULT 'insight',
                source_type TEXT DEFAULT '',
                source_id TEXT DEFAULT '',
                importance REAL DEFAULT 0.5,
                context_tags TEXT DEFAULT '[]',
                embedding TEXT DEFAULT '',
                access_count INTEGER DEFAULT 0,
                last_accessed TEXT,
                is_active INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_entries(memory_type);
            CREATE INDEX IF NOT EXISTS idx_memory_importance ON memory_entries(importance);
            CREATE INDEX IF NOT EXISTS idx_memory_accessed ON memory_entries(last_accessed);
            CREATE TABLE IF NOT EXISTS memory_recall_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT DEFAULT '',
                memory_ids TEXT DEFAULT '[]',
                result_count INTEGER DEFAULT 0,
                context TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
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
            CREATE TABLE IF NOT EXISTS route_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                priority INTEGER NOT NULL DEFAULT 100,
                condition_field TEXT NOT NULL DEFAULT 'keyword',
                condition_operator TEXT NOT NULL DEFAULT 'contains',
                condition_value TEXT NOT NULL,
                target_role_id INTEGER REFERENCES agent_roles(id),
                fallback_role_id INTEGER,
                max_tokens INTEGER DEFAULT 2048,
                temperature REAL DEFAULT 0.7,
                is_active INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_route_priority ON route_rules(priority);
            CREATE TABLE IF NOT EXISTS route_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_text TEXT NOT NULL,
                matched_rule_id INTEGER,
                matched_rule_name TEXT DEFAULT '',
                assigned_role_id INTEGER,
                assigned_role_name TEXT DEFAULT '',
                confidence REAL DEFAULT 0.0,
                response_summary TEXT DEFAULT '',
                tokens_used INTEGER DEFAULT 0,
                latency_ms INTEGER DEFAULT 0,
                source TEXT DEFAULT '',
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_route_logs_role ON route_logs(assigned_role_id);
            CREATE INDEX IF NOT EXISTS idx_route_logs_time ON route_logs(created_at);
            CREATE TABLE IF NOT EXISTS route_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_id INTEGER UNIQUE REFERENCES agent_roles(id),
                total_routed INTEGER DEFAULT 0,
                avg_confidence REAL DEFAULT 0.0,
                avg_tokens REAL DEFAULT 0.0,
                avg_latency_ms REAL DEFAULT 0.0,
                last_routed_at TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_route_stats_role ON route_stats(role_id);
            CREATE TABLE IF NOT EXISTS hcp_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                title TEXT DEFAULT '',
                hospital TEXT DEFAULT '',
                department TEXT DEFAULT '',
                specialty TEXT DEFAULT '',
                city TEXT DEFAULT '',
                tier TEXT DEFAULT 'B',
                traits TEXT DEFAULT '{}',
                prescription_volume REAL DEFAULT 0,
                influence_score REAL DEFAULT 0.5,
                digital_engagement REAL DEFAULT 0.5,
                is_active INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_hcp_tier ON hcp_profiles(tier);
            CREATE INDEX IF NOT EXISTS idx_hcp_specialty ON hcp_profiles(specialty);
            CREATE TABLE IF NOT EXISTS hcp_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hcp_id INTEGER NOT NULL REFERENCES hcp_profiles(id),
                interaction_type TEXT NOT NULL,
                content TEXT DEFAULT '',
                response TEXT DEFAULT '',
                outcome TEXT DEFAULT '',
                strategy_used TEXT DEFAULT '',
                conducted_by INTEGER REFERENCES users(id),
                conducted_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_hcp_int_hcp ON hcp_interactions(hcp_id);
            CREATE INDEX IF NOT EXISTS idx_hcp_int_time ON hcp_interactions(conducted_at);
            CREATE TABLE IF NOT EXISTS hcp_simulations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hcp_id INTEGER NOT NULL REFERENCES hcp_profiles(id),
                scenario TEXT NOT NULL,
                strategy TEXT DEFAULT '',
                expected_outcome TEXT DEFAULT '',
                confidence REAL DEFAULT 0.5,
                suggested_approach TEXT DEFAULT '',
                key_concerns TEXT DEFAULT '',
                recommended_topics TEXT DEFAULT '',
                risk_factors TEXT DEFAULT '',
                simulation_data TEXT DEFAULT '{}',
                status TEXT DEFAULT 'completed',
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_hcp_sim_hcp ON hcp_simulations(hcp_id);
            CREATE TABLE IF NOT EXISTS training_modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'compliance',
                difficulty TEXT NOT NULL DEFAULT 'medium',
                content TEXT DEFAULT '',
                prerequisites TEXT DEFAULT '[]',
                passing_score REAL DEFAULT 0.7,
                estimated_minutes INTEGER DEFAULT 15,
                is_active INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_tm_category ON training_modules(category);
            CREATE INDEX IF NOT EXISTS idx_tm_difficulty ON training_modules(difficulty);
            CREATE TABLE IF NOT EXISTS training_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                module_id INTEGER NOT NULL REFERENCES training_modules(id),
                score REAL DEFAULT 0.0,
                passed INTEGER DEFAULT 0,
                time_spent_seconds INTEGER DEFAULT 0,
                answers TEXT DEFAULT '[]',
                feedback TEXT DEFAULT '',
                difficulty_used TEXT DEFAULT 'medium',
                next_difficulty TEXT DEFAULT '',
                completed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_ts_user ON training_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_ts_module ON training_sessions(module_id);
            CREATE TABLE IF NOT EXISTS training_attributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                training_session_id INTEGER REFERENCES training_sessions(id),
                metric_name TEXT NOT NULL,
                metric_before REAL DEFAULT 0.0,
                metric_after REAL DEFAULT 0.0,
                change_pct REAL DEFAULT 0.0,
                attribution_score REAL DEFAULT 0.0,
                confidence REAL DEFAULT 0.0,
                analysis TEXT DEFAULT '',
                period_days INTEGER DEFAULT 30,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_ta_user ON training_attributions(user_id);
            CREATE INDEX IF NOT EXISTS idx_ta_metric ON training_attributions(metric_name);
            CREATE TABLE IF NOT EXISTS soap_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'general',
                description TEXT DEFAULT '',
                structure TEXT NOT NULL DEFAULT '{}',
                is_active INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS soap_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                template_id INTEGER REFERENCES soap_templates(id),
                subjective TEXT DEFAULT '',
                objective TEXT DEFAULT '',
                assessment TEXT DEFAULT '',
                plan TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'draft',
                priority TEXT DEFAULT 'medium',
                tags TEXT DEFAULT '[]',
                decision_summary TEXT DEFAULT '',
                decided_by INTEGER REFERENCES users(id),
                decided_at TEXT,
                is_active INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_soap_status ON soap_decisions(status);
            CREATE INDEX IF NOT EXISTS idx_soap_priority ON soap_decisions(priority);
            CREATE TABLE IF NOT EXISTS async_mdt_opinions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id INTEGER NOT NULL REFERENCES soap_decisions(id),
                contributor_id INTEGER NOT NULL REFERENCES users(id),
                contributor_role TEXT DEFAULT '',
                opinion TEXT NOT NULL,
                supporting_data TEXT DEFAULT '',
                stance TEXT DEFAULT 'neutral',
                confidence REAL DEFAULT 0.5,
                attachments TEXT DEFAULT '[]',
                is_final INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_async_mdt_decision ON async_mdt_opinions(decision_id);
            CREATE INDEX IF NOT EXISTS idx_async_mdt_contributor ON async_mdt_opinions(contributor_id);
            CREATE TABLE IF NOT EXISTS memory_utility_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_entry_id INTEGER NOT NULL UNIQUE REFERENCES memory_entries(id),
                utility_score REAL DEFAULT 0.0,
                access_frequency REAL DEFAULT 0.0,
                recency_score REAL DEFAULT 0.0,
                importance_score REAL DEFAULT 0.0,
                connectivity_score REAL DEFAULT 0.0,
                decay_rate REAL DEFAULT 0.0,
                last_utility_update TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_mus_score ON memory_utility_scores(utility_score);
            CREATE INDEX IF NOT EXISTS idx_mus_decay ON memory_utility_scores(decay_rate);
            CREATE TABLE IF NOT EXISTS sleep_consolidation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consolidation_type TEXT NOT NULL,
                source_entry_ids TEXT DEFAULT '[]',
                target_entry_id INTEGER REFERENCES memory_entries(id),
                action_detail TEXT DEFAULT '',
                utility_before REAL DEFAULT 0.0,
                utility_after REAL DEFAULT 0.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS working_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                slot_key TEXT NOT NULL,
                slot_value TEXT DEFAULT '',
                slot_type TEXT DEFAULT 'string',
                ttl_seconds INTEGER DEFAULT 1800,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                UNIQUE(session_id, slot_key)
            );
            CREATE INDEX IF NOT EXISTS idx_wm_session ON working_memory(session_id);
            CREATE INDEX IF NOT EXISTS idx_wm_expires ON working_memory(expires_at);
            CREATE TABLE IF NOT EXISTS episodic_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                context TEXT DEFAULT '{}',
                outcome TEXT DEFAULT '',
                valence REAL DEFAULT 0.0,
                intensity REAL DEFAULT 0.5,
                involved_agents TEXT DEFAULT '[]',
                related_entity_type TEXT DEFAULT '',
                related_entity_id INTEGER,
                is_consolidated INTEGER DEFAULT 0,
                created_by TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_em_event ON episodic_memory(event_type);
            CREATE INDEX IF NOT EXISTS idx_em_outcome ON episodic_memory(outcome);
            CREATE INDEX IF NOT EXISTS idx_em_time ON episodic_memory(created_at);
            CREATE TABLE IF NOT EXISTS did_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                did TEXT NOT NULL UNIQUE,
                entity_type TEXT DEFAULT "user",
                entity_id INTEGER,
                public_key TEXT DEFAULT "",
                status TEXT DEFAULT "active",
                metadata TEXT DEFAULT "{}",
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_did_did ON did_registry(did);
            CREATE INDEX IF NOT EXISTS idx_did_status ON did_registry(status);
            CREATE TABLE IF NOT EXISTS vc_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vc_id TEXT NOT NULL UNIQUE,
                issuer_did TEXT NOT NULL REFERENCES did_registry(did),
                subject_did TEXT NOT NULL REFERENCES did_registry(did),
                credential_type TEXT NOT NULL,
                claims TEXT DEFAULT "{}",
                issuance_date TEXT DEFAULT CURRENT_TIMESTAMP,
                expiration_date TEXT,
                proof TEXT DEFAULT "",
                status TEXT DEFAULT "active",
                revoked_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_vc_issuer ON vc_credentials(issuer_did);
            CREATE INDEX IF NOT EXISTS idx_vc_subject ON vc_credentials(subject_did);
            CREATE INDEX IF NOT EXISTS idx_vc_type ON vc_credentials(credential_type);
            CREATE TABLE IF NOT EXISTS fed_audit_contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contributor_did TEXT NOT NULL REFERENCES did_registry(did),
                contribution_type TEXT NOT NULL,
                payload_hash TEXT DEFAULT "",
                payload_summary TEXT DEFAULT "",
                weight REAL DEFAULT 1.0,
                verified INTEGER DEFAULT 0,
                verified_by TEXT DEFAULT "",
                audit_chain_hash TEXT DEFAULT "",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_fed_contributor ON fed_audit_contributions(contributor_did);
            CREATE INDEX IF NOT EXISTS idx_fed_type ON fed_audit_contributions(contribution_type);
            CREATE TABLE IF NOT EXISTS privacy_budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                did TEXT NOT NULL REFERENCES did_registry(did),
                epsilon_total REAL DEFAULT 1.0,
                epsilon_spent REAL DEFAULT 0.0,
                epsilon_remaining REAL DEFAULT 1.0,
                query_count INTEGER DEFAULT 0,
                last_query_at TEXT,
                reset_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_pb_did ON privacy_budgets(did);
            CREATE TABLE IF NOT EXISTS data_masking_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL UNIQUE,
                field_pattern TEXT NOT NULL,
                masking_type TEXT NOT NULL,
                masking_config TEXT DEFAULT "{}",
                applies_to TEXT DEFAULT "all",
                enabled INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS dp_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                did TEXT NOT NULL REFERENCES did_registry(did),
                operation_type TEXT NOT NULL,
                epsilon_consumed REAL DEFAULT 0.0,
                data_category TEXT DEFAULT "",
                row_count INTEGER DEFAULT 0,
                noise_level REAL DEFAULT 0.0,
                approved INTEGER DEFAULT 1,
                details TEXT DEFAULT "{}",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_dpal_did ON dp_audit_log(did);
            CREATE INDEX IF NOT EXISTS idx_dpal_type ON dp_audit_log(operation_type);

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

            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                persona_type TEXT DEFAULT \"\",
                specialization TEXT DEFAULT \"\",
                experience_level TEXT DEFAULT \"mid\",
                preferred_content_types TEXT DEFAULT \"[]\",
                custom_tags TEXT DEFAULT \"[]\",
                embedding TEXT DEFAULT \"\",
                updated_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_up_user ON user_profiles(user_id);

            CREATE TABLE IF NOT EXISTS user_behaviors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                action_type TEXT NOT NULL,
                target_type TEXT DEFAULT \"\",
                target_id TEXT DEFAULT \"\",
                metadata TEXT DEFAULT \"{}\",
                session_id TEXT DEFAULT \"\",
                duration_seconds INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_ub_user ON user_behaviors(user_id);
            CREATE INDEX IF NOT EXISTS idx_ub_action ON user_behaviors(action_type);
            CREATE INDEX IF NOT EXISTS idx_ub_target ON user_behaviors(target_type);

            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                rec_type TEXT NOT NULL,
                rec_target_id TEXT DEFAULT \"\",
                rec_title TEXT DEFAULT \"\",
                rec_reason TEXT DEFAULT \"\",
                score REAL DEFAULT 0.0,
                strategy_name TEXT DEFAULT \"\",
                clicked INTEGER DEFAULT 0,
                dismissed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_rec_user ON recommendations(user_id);
            CREATE INDEX IF NOT EXISTS idx_rec_type ON recommendations(rec_type);
            CREATE TABLE IF NOT EXISTS agent_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT NOT NULL,
                agent_role TEXT NOT NULL,
                description TEXT DEFAULT \"\",
                entity_types TEXT DEFAULT \"[]\",
                capabilities TEXT DEFAULT \"[]\",
                confidence REAL DEFAULT 0.5,
                priority INTEGER DEFAULT 100,
                enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_ask_role ON agent_skills(agent_role);
            CREATE INDEX IF NOT EXISTS idx_ask_entity ON agent_skills(entity_types);
            CREATE TABLE IF NOT EXISTS collaboration_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL UNIQUE,
                task_description TEXT DEFAULT \"\",
                source_entity_id TEXT,
                source_agent_role TEXT DEFAULT \"\",
                orchestrator_agent TEXT DEFAULT \"\",
                status TEXT DEFAULT \"active\",
                involved_agents TEXT DEFAULT \"[]\",
                routing_strategy TEXT DEFAULT \"semantic\",
                total_steps INTEGER DEFAULT 0,
                completed_steps INTEGER DEFAULT 0,
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                result_summary TEXT DEFAULT \"\"
            );
            CREATE INDEX IF NOT EXISTS idx_cs_session ON collaboration_sessions(session_id);
            CREATE INDEX IF NOT EXISTS idx_cs_status ON collaboration_sessions(status);
            CREATE TABLE IF NOT EXISTS collaboration_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES collaboration_sessions(session_id),
                step_order INTEGER NOT NULL,
                agent_role TEXT NOT NULL,
                action_type TEXT DEFAULT \"process\",
                input_summary TEXT DEFAULT \"\",
                output_summary TEXT DEFAULT \"\",
                entity_id TEXT,
                status TEXT DEFAULT \"pending\",
                started_at TEXT,
                completed_at TEXT,
                duration_seconds INTEGER DEFAULT 0,
                metadata TEXT DEFAULT \"{}\"
            );
            CREATE INDEX IF NOT EXISTS idx_cstep_session ON collaboration_steps(session_id);

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

            CREATE TABLE IF NOT EXISTS memory_consolidation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consolidation_type TEXT NOT NULL,
                source_table TEXT DEFAULT \"\",
                item_count INTEGER DEFAULT 0,
                items_promoted INTEGER DEFAULT 0,
                items_pruned INTEGER DEFAULT 0,
                items_superseded INTEGER DEFAULT 0,
                duration_ms INTEGER DEFAULT 0,
                status TEXT DEFAULT \"completed\",
                details TEXT DEFAULT \"{}\",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS agent_execution_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE,
                source TEXT DEFAULT "internal",
                session_id TEXT DEFAULT "",
                agent_role TEXT DEFAULT "",
                action_type TEXT DEFAULT "process",
                input_data TEXT DEFAULT "{}",
                output_data TEXT DEFAULT "{}",
                status TEXT DEFAULT "pending",
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                result_verified INTEGER DEFAULT 0,
                verification_detail TEXT DEFAULT "",
                requires_human_approval INTEGER DEFAULT 0,
                assigned_to TEXT DEFAULT "",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                duration_ms INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_aet_task ON agent_execution_tasks(task_id);
            CREATE INDEX IF NOT EXISTS idx_aet_status ON agent_execution_tasks(status);
            CREATE INDEX IF NOT EXISTS idx_aet_session ON agent_execution_tasks(session_id);

            CREATE TABLE IF NOT EXISTS mcp_tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_name TEXT UNIQUE,
                description TEXT DEFAULT "",
                tool_version TEXT DEFAULT "1.0.0",
                endpoint_url TEXT DEFAULT "",
                input_schema TEXT DEFAULT "{}",
                output_schema TEXT DEFAULT "{}",
                auth_required INTEGER DEFAULT 0,
                enabled INTEGER DEFAULT 1,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_mcp_name ON mcp_tools(tool_name);

            CREATE TABLE IF NOT EXISTS mcp_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_name TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                user_role TEXT DEFAULT "",
                params TEXT DEFAULT "{}",
                result TEXT DEFAULT "{}",
                granted INTEGER DEFAULT 0,
                reason TEXT DEFAULT "",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_mcp_audit_tool ON mcp_audit_log(tool_name);
            CREATE INDEX IF NOT EXISTS idx_mcp_audit_user ON mcp_audit_log(user_id);
            CREATE INDEX IF NOT EXISTS idx_mcp_audit_at ON mcp_audit_log(created_at);

            CREATE TABLE IF NOT EXISTS orchestration_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT UNIQUE,
                description TEXT DEFAULT "",
                steps TEXT DEFAULT "[]",
                version TEXT DEFAULT "1.0.0",
                enabled INTEGER DEFAULT 1,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_ot_name ON orchestration_templates(template_name);

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

            CREATE TABLE IF NOT EXISTS training_scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                script_id TEXT UNIQUE,
                script_name TEXT,
                source_agent_role TEXT,
                source_collaboration_id TEXT,
                description TEXT,
                steps TEXT DEFAULT "[]",
                difficulty TEXT DEFAULT "mid",
                target_roles TEXT DEFAULT "[]",
                score REAL,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_ts_script ON training_scripts(script_id);
            CREATE INDEX IF NOT EXISTS idx_ts_role ON training_scripts(source_agent_role);

            CREATE TABLE IF NOT EXISTS training_roi_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id TEXT UNIQUE,
                period_start TEXT,
                period_end TEXT,
                training_hours REAL,
                participants INTEGER,
                behavior_change_score REAL,
                sales_impact REAL,
                cost_savings REAL,
                roi REAL,
                metadata TEXT DEFAULT "{}",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_tra_id ON training_roi_analysis(analysis_id);

            CREATE TABLE IF NOT EXISTS effect_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_id TEXT UNIQUE,
                agent_role TEXT,
                metric_type TEXT,
                metric_value REAL,
                metric_unit TEXT,
                source_table TEXT,
                source_row_id TEXT,
                source_sub TEXT DEFAULT '',
                period_start TEXT,
                period_end TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_em_agent ON effect_metrics(agent_role);
            CREATE INDEX IF NOT EXISTS idx_em_source_sub ON effect_metrics(source_sub);

            CREATE TABLE IF NOT EXISTS benchmark_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT UNIQUE,
                report_name TEXT,
                report_type TEXT,
                data_source TEXT DEFAULT "aggregated",
                summary TEXT,
                metrics TEXT DEFAULT "{}",
                period TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_br_report ON benchmark_reports(report_id);

            CREATE TABLE IF NOT EXISTS agent_marketplace (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT UNIQUE,
                item_name TEXT,
                item_type TEXT DEFAULT "template",
                description TEXT,
                agent_config TEXT DEFAULT "{}",
                category TEXT,
                price_model TEXT DEFAULT "free",
                rating REAL,
                download_count INTEGER,
                enabled INTEGER,
                publisher TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_am_item ON agent_marketplace(item_id);
            CREATE INDEX IF NOT EXISTS idx_am_cat ON agent_marketplace(category);

            CREATE TABLE IF NOT EXISTS supply_chain_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT UNIQUE,
                item_name TEXT,
                sku TEXT,
                category TEXT,
                current_stock INTEGER,
                min_stock INTEGER,
                max_stock INTEGER,
                unit_price REAL,
                supplier TEXT,
                status TEXT DEFAULT "active",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_sci_item ON supply_chain_items(item_id);

            CREATE TABLE IF NOT EXISTS sensor_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
                session_name TEXT,
                event_type TEXT DEFAULT "academic_meeting",
                location TEXT,
                start_time TEXT,
                end_time TEXT,
                data_summary TEXT DEFAULT "{}",
                status TEXT DEFAULT "active",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_ss_session ON sensor_sessions(session_id);

            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL DEFAULT "",
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS token_budget (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                model TEXT NOT NULL,
                daily_used INTEGER NOT NULL DEFAULT 0,
                alert_sent INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_token_budget_user ON token_budget(user_id, model);

            CREATE TABLE IF NOT EXISTS token_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                model TEXT NOT NULL,
                tokens INTEGER NOT NULL DEFAULT 0,
                cost REAL NOT NULL DEFAULT 0.0,
                usage_date TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_token_usage_user ON token_usage(user_id, model, usage_date);
"""
