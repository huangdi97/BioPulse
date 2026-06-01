from cloud.shared.repository import BaseRepository
from cloud.shared.columns import (
    TABLE_AGENT_EXECUTION_TASKS_COLS,
    TABLE_AGENT_MARKETPLACE_COLS,
    TABLE_AGENT_PIPELINES_COLS,
    TABLE_AGENT_ROLES_COLS,
    TABLE_AGENT_SKILLS_COLS,
    TABLE_ASYNC_MDT_OPINIONS_COLS,
    TABLE_AUDIT_CHAIN_ENTRIES_COLS,
    TABLE_AUDIT_LOGS_COLS,
    TABLE_BENCHMARK_REPORTS_COLS,
    TABLE_BOARD_TASKS_COLS,
    TABLE_CAUSAL_ANALYSES_COLS,
    TABLE_CAUSAL_GRAPHS_COLS,
    TABLE_COLLABORATION_SESSIONS_COLS,
    TABLE_COLLABORATION_STEPS_COLS,
    TABLE_COMPLIANCE_AUDIT_RECORDS_COLS,
    TABLE_COMPLIANCE_RULES_COLS,
    TABLE_CONTENTS_COLS,
    TABLE_COUNTERFACTUAL_SCENARIOS_COLS,
    TABLE_CROSS_CASE_INSIGHTS_COLS,
    TABLE_CUSTOMER_INTERACTIONS_COLS,
    TABLE_CUSTOMERS_COLS,
    TABLE_DATA_MASKING_RULES_COLS,
    TABLE_DECISION_CASES_COLS,
    TABLE_DP_AUDIT_LOG_COLS,
    TABLE_EFFECT_METRICS_COLS,
    TABLE_EPISODIC_MEMORY_COLS,
    TABLE_EVENT_BUS_DEFINITIONS_COLS,
    TABLE_EVENT_BUS_MESSAGES_COLS,
    TABLE_EVENT_DELIVERY_LOG_COLS,
    TABLE_FED_AUDIT_CONTRIBUTIONS_COLS,
    TABLE_FEDERATED_ROUNDS_COLS,
    TABLE_HCP_INTERACTIONS_COLS,
    TABLE_HCP_PROFILES_COLS,
    TABLE_HCP_SIMULATIONS_COLS,
    TABLE_KG_ENTITIES_COLS,
    TABLE_KG_RELATIONS_COLS,
    TABLE_KG_SEARCH_CACHE_COLS,
    TABLE_MARKET_INTEL_ITEMS_COLS,
    TABLE_MARKET_INTEL_SOURCES_COLS,
    TABLE_MCP_TOOLS_COLS,
    TABLE_MDT_OPINIONS_COLS,
    TABLE_MDT_PARTICIPANTS_COLS,
    TABLE_MDT_SESSIONS_COLS,
    TABLE_MEMORY_CONSOLIDATION_LOG_COLS,
    TABLE_MEMORY_ENTRIES_COLS,
    TABLE_MEMORY_GATES_COLS,
    TABLE_MEMORY_RECALL_LOG_COLS,
    TABLE_MEMORY_UTILITY_SCORES_COLS,
    TABLE_NMPA_COMPLIANCE_LOGS_COLS,
    TABLE_NODE_MEMORY_LINKS_COLS,
    TABLE_NOTIFICATION_TEMPLATES_COLS,
    TABLE_NOTIFICATIONS_COLS,
    TABLE_OPPORTUNITIES_COLS,
    TABLE_ORCHESTRATION_TEMPLATES_COLS,
    TABLE_PIPELINE_RUNS_COLS,
    TABLE_PIPELINE_STEP_RUNS_COLS,
    TABLE_PIPELINE_STEPS_COLS,
    TABLE_PRIVACY_BUDGETS_COLS,
    TABLE_PRIVACY_COMPUTE_JOBS_COLS,
    TABLE_RECOMMENDATIONS_COLS,
    TABLE_ROUTE_LOGS_COLS,
    TABLE_ROUTE_RULES_COLS,
    TABLE_ROUTE_STATS_COLS,
    TABLE_SLEEP_CONSOLIDATION_LOGS_COLS,
    TABLE_SOAP_DECISIONS_COLS,
    TABLE_SOAP_TEMPLATES_COLS,
    TABLE_TASK_BOARDS_COLS,
    TABLE_TEAMS_COLS,
    TABLE_TRAINING_ATTRIBUTIONS_COLS,
    TABLE_TRAINING_CORRECTIONS_COLS,
    TABLE_TRAINING_MODULES_COLS,
    TABLE_TRAINING_ROI_ANALYSIS_COLS,
    TABLE_TRAINING_SCRIPTS_COLS,
    TABLE_TRAINING_SESSIONS_COLS,
    TABLE_USER_BEHAVIORS_COLS,
    TABLE_USER_PROFILES_COLS,
    TABLE_USER_TEAM_COLS,
    TABLE_USERS_COLS,
    TABLE_WORKING_MEMORY_COLS,
    TABLE_WORLD_TREE_NODES_COLS,
    TABLE_WORLD_TREE_SNAPSHOTS_COLS,
)


class AgentExecutionTasksRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "agent_execution_tasks", TABLE_AGENT_EXECUTION_TASKS_COLS)

    def get_by_task_id(self, task_id: str):
        placeholders = ", ".join(self.cols)
        query = f"SELECT {placeholders} FROM {self.table_name} WHERE task_id = ?"
        cursor = self.db.execute(query, (task_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


class AgentMarketplaceRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "agent_marketplace", TABLE_AGENT_MARKETPLACE_COLS)

    def list_filtered(self, category=None, price_model=None, enabled=None) -> list:
        placeholders = ", ".join(self.cols)
        conditions, params = [], []
        if category:
            conditions.append("category = ?")
            params.append(category)
        if price_model:
            conditions.append("price_model = ?")
            params.append(price_model)
        if enabled is not None:
            conditions.append("enabled = ?")
            params.append(enabled)
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name}{where} ORDER BY rating DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]


class AgentPipelinesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "agent_pipelines", TABLE_AGENT_PIPELINES_COLS)


class AgentRolesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "agent_roles", TABLE_AGENT_ROLES_COLS)

    def list_active(self, limit: int = 5) -> list:
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE is_active=1 LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_system_prompt(self, role_id: int):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE id=?", (role_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_by_id(self, role_id: int):
        return super().get_by_id(role_id)


class AgentSkillsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "agent_skills", TABLE_AGENT_SKILLS_COLS)


class AsyncMdtOpinionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "async_mdt_opinions", TABLE_ASYNC_MDT_OPINIONS_COLS)

    def list_by_decision(self, decision_id: int):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE decision_id=? ORDER BY created_at ASC",
            (decision_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]


class AuditChainEntriesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "audit_chain_entries", TABLE_AUDIT_CHAIN_ENTRIES_COLS)


class AuditLogsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "audit_logs", TABLE_AUDIT_LOGS_COLS)


class BenchmarkReportsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "benchmark_reports", TABLE_BENCHMARK_REPORTS_COLS)

    def list_by_report_type(self, report_type=None) -> list:
        placeholders = ", ".join(self.cols)
        where = ""
        params = []
        if report_type:
            where = "WHERE report_type = ?"
            params.append(report_type)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name}{where} ORDER BY created_at DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]


class BoardTasksRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "board_tasks", TABLE_BOARD_TASKS_COLS)

    def get_by_board_and_id(self, board_id: int, task_id: int):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE id=? AND board_id=?",
            (task_id, board_id),
        ).fetchone()
        return dict(row) if row else None

    def list_by_board(self, board_id: int, status_filter=None):
        conditions = ["board_id=?", "is_active=1"]
        params = [board_id]
        if status_filter:
            conditions.append("status=?")
            params.append(status_filter)
        return self.list_all(
            conditions=conditions,
            params=params,
            order_by="sort_order ASC, created_at DESC",
        )

    def list_by_assignee(self, user_id: int):
        placeholders = ", ".join(f"bt.{c}" for c in self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders}, tb.name as board_name FROM {self.table_name} bt "
            "LEFT JOIN task_boards tb ON bt.board_id = tb.id "
            "WHERE bt.assignee_id=? AND bt.is_active=1 AND tb.is_active=1 "
            "ORDER BY bt.created_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


class CausalAnalysesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "causal_analyses", TABLE_CAUSAL_ANALYSES_COLS)

    def list_by_case_id(self, case_id: int):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE case_id=? ORDER BY created_at DESC",
            (case_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def count_distinct_case_ids(self):
        return self.db.execute(
            "SELECT COUNT(DISTINCT case_id) FROM causal_analyses ca "
            "JOIN decision_cases dc ON ca.case_id=dc.id WHERE dc.is_active=1"
        ).fetchone()[0]


class CausalGraphsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "causal_graphs", TABLE_CAUSAL_GRAPHS_COLS)


class CollaborationSessionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(
            db, "collaboration_sessions", TABLE_COLLABORATION_SESSIONS_COLS
        )


class CollaborationStepsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "collaboration_steps", TABLE_COLLABORATION_STEPS_COLS)


class ComplianceAuditRecordsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(
            db, "compliance_audit_records", TABLE_COMPLIANCE_AUDIT_RECORDS_COLS
        )


class ComplianceRulesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "compliance_rules", TABLE_COMPLIANCE_RULES_COLS)


class ContentsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "contents", TABLE_CONTENTS_COLS)


class CounterfactualScenariosRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(
            db, "counterfactual_scenarios", TABLE_COUNTERFACTUAL_SCENARIOS_COLS
        )


class CrossCaseInsightsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "cross_case_insights", TABLE_CROSS_CASE_INSIGHTS_COLS)

    def list_filtered(
        self, insight_type=None, confidence_min=None, page=1, page_size=20
    ):
        conditions = ["is_active=1"]
        params = []
        if insight_type:
            conditions.append("insight_type=?")
            params.append(insight_type)
        if confidence_min is not None:
            conditions.append("confidence >= ?")
            params.append(confidence_min)
        return self.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params or None,
            order_by="confidence DESC",
        )

    def get_active_by_id(self, insight_id: int):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE id=? AND is_active=1",
            (insight_id,),
        ).fetchone()
        return dict(row) if row else None

    def count_by_type(self):
        rows = self.db.execute(
            f"SELECT insight_type, COUNT(*) AS cnt FROM {self.table_name} WHERE is_active=1 "
            "GROUP BY insight_type"
        ).fetchall()
        return [{"type": r["insight_type"], "count": r["cnt"]} for r in rows]

    def top_by_confidence(self, limit=5):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE is_active=1 ORDER BY confidence DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


class CustomerInteractionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "customer_interactions", TABLE_CUSTOMER_INTERACTIONS_COLS)

    def list_by_customer_id(self, customer_id: int):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE customer_id=? ORDER BY conducted_at DESC",
            (customer_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_filtered(self, type_=None, conducted_by=None, page=1, page_size=20):
        conditions, params = [], []
        if type_:
            conditions.append("type=?")
            params.append(type_)
        if conducted_by is not None:
            conditions.append("conducted_by=?")
            params.append(conducted_by)
        return self.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions or None,
            params=params or None,
            order_by="conducted_at DESC",
        )


class CustomersRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "customers", TABLE_CUSTOMERS_COLS)

    def exists(self, customer_id: int):
        return (
            self.db.execute(
                f"SELECT id FROM {self.table_name} WHERE id=?", (customer_id,)
            ).fetchone()
            is not None
        )


class DataMaskingRulesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "data_masking_rules", TABLE_DATA_MASKING_RULES_COLS)


class DecisionCasesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "decision_cases", TABLE_DECISION_CASES_COLS)

    def get_active_by_id(self, case_id: int):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE id=? AND is_active=1",
            (case_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_filtered(
        self,
        outcome_score_min=None,
        outcome_score_max=None,
        tag=None,
        search=None,
        page=1,
        page_size=20,
    ):
        conditions = ["is_active=1"]
        params = []
        if outcome_score_min is not None:
            conditions.append("outcome_score >= ?")
            params.append(outcome_score_min)
        if outcome_score_max is not None:
            conditions.append("outcome_score <= ?")
            params.append(outcome_score_max)
        if tag:
            conditions.append("tags LIKE ?")
            params.append(f"%{tag}%")
        if search:
            conditions.append("(name LIKE ? OR description LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        return self.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params or None,
            order_by="created_at DESC",
        )

    def soft_delete_with_causal(self, case_id: int):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute(
            f"UPDATE {self.table_name} SET is_active=0, updated_at=? WHERE id=?",
            (now, case_id),
        )
        self.db.execute(
            "UPDATE causal_analyses SET case_id=-case_id WHERE case_id=?", (case_id,)
        )
        self.db.commit()

    def list_success_cases(self, limit=5, filter_tags=None):
        conditions = ["is_active=1", "outcome_score >= 0.5"]
        params = []
        if filter_tags:
            tc = " OR ".join(["tags LIKE ?"] * len(filter_tags))
            conditions.append(f"({tc})")
            params = [f"%{t}%" for t in filter_tags]
        placeholders = ", ".join(self.cols)
        where = " WHERE " + " AND ".join(conditions)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name}{where} ORDER BY outcome_score DESC LIMIT ?",
            params + [limit],
        ).fetchall()
        return [dict(r) for r in rows]

    def list_fail_cases(self, limit=5, filter_tags=None):
        conditions = ["is_active=1", "outcome_score <= -0.5"]
        params = []
        if filter_tags:
            tc = " OR ".join(["tags LIKE ?"] * len(filter_tags))
            conditions.append(f"({tc})")
            params = [f"%{t}%" for t in filter_tags]
        placeholders = ", ".join(self.cols)
        where = " WHERE " + " AND ".join(conditions)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name}{where} ORDER BY outcome_score ASC LIMIT ?",
            params + [limit],
        ).fetchall()
        return [dict(r) for r in rows]

    def count_active(self):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE is_active=1"
        ).fetchone()[0]

    def score_distribution(self):
        rows = self.db.execute(
            "SELECT CASE WHEN outcome_score <= -0.5 THEN 'fail(<=-0.5)' "
            "WHEN outcome_score < 0 THEN 'negative(-0.5~0)' WHEN outcome_score = 0 THEN 'neutral(0)' "
            "WHEN outcome_score < 0.5 THEN 'positive(0~0.5)' ELSE 'success(>=0.5)' END AS bucket, "
            "COUNT(*) AS cnt FROM decision_cases WHERE is_active=1 GROUP BY bucket ORDER BY bucket"
        ).fetchall()
        return [{"bucket": r["bucket"], "count": r["cnt"]} for r in rows]


class DpAuditLogRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "dp_audit_log", TABLE_DP_AUDIT_LOG_COLS)


class EffectMetricsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "effect_metrics", TABLE_EFFECT_METRICS_COLS)

    def dashboard(self, agent_role=None) -> list:
        where = ""
        params = []
        if agent_role:
            where = "WHERE agent_role = ?"
            params.append(agent_role)
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT agent_role, metric_type, SUM(metric_value) AS total, AVG(metric_value) AS avg_value "
            f"FROM {self.table_name} {where} GROUP BY agent_role, metric_type ORDER BY agent_role, metric_type",
            params,
        ).fetchall()
        return [dict(r) for r in rows]


class EpisodicMemoryRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "episodic_memory", TABLE_EPISODIC_MEMORY_COLS)

    def find_unconsolidated(self):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} "
            "WHERE is_consolidated=0 OR is_consolidated IS NULL"
        ).fetchall()
        return [dict(r) for r in rows]

    def count_by_creator(self, creator_id):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE created_by=?",
            (creator_id,),
        ).fetchone()[0]


class EventBusDefinitionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "event_bus_definitions", TABLE_EVENT_BUS_DEFINITIONS_COLS)

    def get_by_event_type(self, event_type: str):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE event_type=?",
            (event_type,),
        ).fetchone()
        return dict(row) if row else None

    def list_filtered(self, source_end=None, enabled=None):
        conditions = ["1=1"]
        params = []
        if source_end:
            conditions.append("source_end=?")
            params.append(source_end)
        if enabled is not None:
            conditions.append("enabled=?")
            params.append(enabled)
        placeholders = ", ".join(self.cols)
        where = " AND ".join(conditions)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE {where} ORDER BY priority ASC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def toggle_enabled(self, event_type: str):
        self.db.execute(
            "UPDATE event_bus_definitions SET enabled = CASE WHEN enabled=1 THEN 0 ELSE 1 END WHERE event_type=?",
            (event_type,),
        )
        self.db.commit()

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]


class EventBusMessagesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "event_bus_messages", TABLE_EVENT_BUS_MESSAGES_COLS)

    def get_by_message_id(self, message_id: str):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE message_id=?",
            (message_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_filtered(
        self,
        event_type=None,
        status=None,
        source_end=None,
        start_date=None,
        end_date=None,
    ):
        conditions = ["1=1"]
        params = []
        if event_type:
            conditions.append("event_type=?")
            params.append(event_type)
        if status:
            conditions.append("status=?")
            params.append(status)
        if source_end:
            conditions.append("source_end=?")
            params.append(source_end)
        if start_date:
            conditions.append("created_at >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date)
        placeholders = ", ".join(self.cols)
        where = " AND ".join(conditions)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE {where} ORDER BY created_at DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def mark_delivered(self, message_id: str):
        self.db.execute(
            "UPDATE event_bus_messages SET status='delivered', delivered_at=CURRENT_TIMESTAMP WHERE message_id=?",
            (message_id,),
        )
        self.db.commit()

    def mark_pending_with_retry(self, message_id: str):
        self.db.execute(
            "UPDATE event_bus_messages SET status='pending', retry_count=retry_count+1 WHERE message_id=?",
            (message_id,),
        )
        self.db.commit()

    def count_by_status(self):
        return {
            "pending": self.db.execute(
                f"SELECT COUNT(*) FROM {self.table_name} WHERE status='pending'"
            ).fetchone()[0],
            "delivered": self.db.execute(
                f"SELECT COUNT(*) FROM {self.table_name} WHERE status='delivered'"
            ).fetchone()[0],
            "failed": self.db.execute(
                f"SELECT COUNT(*) FROM {self.table_name} WHERE status='failed'"
            ).fetchone()[0],
        }

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]

    def top_event_types(self, limit=5):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT event_type, COUNT(*) as cnt FROM {self.table_name} "
            "GROUP BY event_type ORDER BY cnt DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_recent(self, limit=5):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


class EventDeliveryLogRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "event_delivery_log", TABLE_EVENT_DELIVERY_LOG_COLS)

    def list_filtered(self, message_id=None, target_end=None, delivery_status=None):
        conditions = ["1=1"]
        params = []
        if message_id:
            conditions.append("message_id=?")
            params.append(message_id)
        if target_end:
            conditions.append("target_end=?")
            params.append(target_end)
        if delivery_status:
            conditions.append("delivery_status=?")
            params.append(delivery_status)
        placeholders = ", ".join(self.cols)
        where = " AND ".join(conditions)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE {where} ORDER BY id",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def list_by_message_id(self, message_id: str):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE message_id=? ORDER BY id",
            (message_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def reset_pending_by_message(self, message_id: str):
        self.db.execute(
            "UPDATE event_delivery_log SET delivery_status='pending', error_message='', "
            "response_summary='', attempt=attempt+1 WHERE message_id=?",
            (message_id,),
        )
        self.db.commit()

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]

    def count_by_status(self):
        return {
            "delivered": self.db.execute(
                f"SELECT COUNT(*) FROM {self.table_name} WHERE delivery_status='delivered'"
            ).fetchone()[0],
            "pending": self.db.execute(
                f"SELECT COUNT(*) FROM {self.table_name} WHERE delivery_status='pending'"
            ).fetchone()[0],
        }


class FedAuditContributionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(
            db, "fed_audit_contributions", TABLE_FED_AUDIT_CONTRIBUTIONS_COLS
        )

    def list_filtered(
        self, contributor_did=None, contribution_type=None, verified=None
    ):
        conditions, params = [], []
        if contributor_did:
            conditions.append("contributor_did=?")
            params.append(contributor_did)
        if contribution_type:
            conditions.append("contribution_type=?")
            params.append(contribution_type)
        if verified is not None:
            conditions.append("verified=?")
            params.append(verified)
        return self.list_all(
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )

    def get_latest_by_did_and_type(self, contributor_did: str, contribution_type: str):
        row = self.db.execute(
            f"SELECT {', '.join(self.cols)} FROM {self.table_name} "
            "WHERE contributor_did=? AND contribution_type=? ORDER BY id DESC LIMIT 1",
            (contributor_did, contribution_type),
        ).fetchone()
        return dict(row) if row else None

    def get_recent(self, limit: int = 5):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]


class FederatedRoundsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "federated_rounds", TABLE_FEDERATED_ROUNDS_COLS)


class HcpInteractionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "hcp_interactions", TABLE_HCP_INTERACTIONS_COLS)

    def count_by_hcp_id(self, hcp_id: int):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE hcp_id=?", (hcp_id,)
        ).fetchone()[0]

    def get_last_by_hcp_id(self, hcp_id: int):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE hcp_id=? ORDER BY conducted_at DESC LIMIT 1",
            (hcp_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_by_hcp_id(self, hcp_id: int, page=1, page_size=20):
        conditions = ["hcp_id=?"]
        params = [hcp_id]
        return self.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params,
            order_by="conducted_at DESC",
        )

    def get_recent_by_hcp_id(self, hcp_id: int, limit: int = 5):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE hcp_id=? ORDER BY conducted_at DESC LIMIT ?",
            (hcp_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


class HcpProfilesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "hcp_profiles", TABLE_HCP_PROFILES_COLS)

    def list_filtered(self, tier=None, specialty=None, city=None, page=1, page_size=20):
        conditions, params = [], []
        if tier:
            conditions.append("tier=?")
            params.append(tier)
        if specialty:
            conditions.append("specialty=?")
            params.append(specialty)
        if city:
            conditions.append("city=?")
            params.append(city)
        return self.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions or None,
            params=params or None,
        )

    def count_active(self):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE is_active=1"
        ).fetchone()[0]

    def tier_distribution(self):
        rows = self.db.execute(
            f"SELECT tier, COUNT(*) as cnt FROM {self.table_name} WHERE is_active=1 GROUP BY tier"
        ).fetchall()
        return {r["tier"]: r["cnt"] for r in rows}


class HcpSimulationsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "hcp_simulations", TABLE_HCP_SIMULATIONS_COLS)

    def count_by_hcp_id(self, hcp_id: int):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE hcp_id=?", (hcp_id,)
        ).fetchone()[0]

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]

    def get_recent(self, limit: int = 5):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_filtered(self, hcp_id=None, status_=None, page=1, page_size=20):
        conditions, params = [], []
        if hcp_id is not None:
            conditions.append("hcp_id=?")
            params.append(hcp_id)
        if status_:
            conditions.append("status=?")
            params.append(status_)
        return self.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )


class KgEntitiesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "kg_entities", TABLE_KG_ENTITIES_COLS)

    def get_by_entity_id(self, entity_id: str):
        row = self.db.execute(
            f"SELECT {', '.join(self.cols)} FROM {self.table_name} WHERE entity_id=?",
            (entity_id,),
        ).fetchone()
        return dict(row) if row else None

    def exists_entity_id(self, entity_id: str):
        return (
            self.db.execute(
                f"SELECT id FROM {self.table_name} WHERE entity_id=?", (entity_id,)
            ).fetchone()
            is not None
        )

    def list_filtered(self, entity_type=None, name=None, status_="active"):
        conditions, params = [], []
        if entity_type:
            conditions.append("entity_type=?")
            params.append(entity_type)
        if name:
            conditions.append("name LIKE ?")
            params.append(f"%{name}%")
        if status_:
            conditions.append("status=?")
            params.append(status_)
        return self.list_all(
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )

    def search_by_name_and_types(self, query: str, entity_types=None, limit: int = 20):
        conditions = ["status='active'", "name LIKE ?"]
        params: list = [f"%{query}%"]
        if entity_types:
            ph = ",".join(["?"] * len(entity_types))
            conditions.append(f"entity_type IN ({ph})")
            params.extend(entity_types)
        placeholders = ", ".join(self.cols)
        where = " WHERE " + " AND ".join(conditions)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name}{where} LIMIT {limit}",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def count_active(self):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE status='active'"
        ).fetchone()[0]

    def count_by_entity_type(self):
        rows = self.db.execute(
            f"SELECT entity_type, COUNT(*) as cnt FROM {self.table_name} WHERE status='active' GROUP BY entity_type"
        ).fetchall()
        return [{"type": r["entity_type"], "count": r["cnt"]} for r in rows]

    def soft_delete_by_entity_id(self, entity_id: str) -> bool:
        cursor = self.db.execute(
            f"UPDATE {self.table_name} SET status='inactive', updated_at=CURRENT_TIMESTAMP WHERE entity_id=?",
            (entity_id,),
        )
        self.db.commit()
        return cursor.rowcount > 0

    def top_active(self, limit: int = 5):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} "
            "WHERE status='active' ORDER BY confidence DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


class KgRelationsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "kg_relations", TABLE_KG_RELATIONS_COLS)

    def list_by_entity_id(self, entity_id: str):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE source_entity_id=? OR target_entity_id=?",
            (entity_id, entity_id),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_filtered(self, source=None, target=None, relation_type=None):
        conditions, params = [], []
        if source:
            conditions.append("source_entity_id=?")
            params.append(source)
        if target:
            conditions.append("target_entity_id=?")
            params.append(target)
        if relation_type:
            conditions.append("relation_type=?")
            params.append(relation_type)
        return self.list_all(
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )

    def list_by_entity_ids_batch(self, entity_ids):
        if not entity_ids:
            return []
        ph = ",".join(["?"] * len(entity_ids))
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE source_entity_id IN ({ph}) OR target_entity_id IN ({ph})",
            entity_ids + entity_ids,
        ).fetchall()
        return [dict(r) for r in rows]

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]

    def count_by_relation_type(self):
        rows = self.db.execute(
            f"SELECT relation_type, COUNT(*) as cnt FROM {self.table_name} GROUP BY relation_type"
        ).fetchall()
        return [{"type": r["relation_type"], "count": r["cnt"]} for r in rows]

    def top_connected(self, limit: int = 10):
        rows = self.db.execute(
            f"""SELECT e.name, e.entity_type, COUNT(r.id) as degree FROM kg_entities e
                LEFT JOIN {self.table_name} r ON e.entity_id=r.source_entity_id OR e.entity_id=r.target_entity_id
                WHERE e.status='active' GROUP BY e.entity_id ORDER BY degree DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [
            {"name": r["name"], "type": r["entity_type"], "degree": r["degree"]}
            for r in rows
        ]


class KgSearchCacheRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "kg_search_cache", TABLE_KG_SEARCH_CACHE_COLS)

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]


class MarketIntelItemsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "market_intel_items", TABLE_MARKET_INTEL_ITEMS_COLS)

    def count_by_field(self, field: str) -> dict:
        if field not in self.cols:
            return {}
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {field}, COUNT(*) as cnt FROM {self.table_name} GROUP BY {field}"
        ).fetchall()

    def count_recent_critical(self, limit: int = 10) -> list:
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE impact_level='critical' ORDER BY collected_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def count_by_date_range(self, days: int = 7) -> list:
        from datetime import datetime, timedelta

        result = []
        placeholders = ", ".join(self.cols)
        for i in range(days, -1, -1):
            day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            cnt = self.db.execute(
                f"SELECT COUNT(*) FROM {self.table_name} WHERE date(collected_at)=?",
                (day,),
            ).fetchone()[0]
            result.append({"date": day, "count": cnt})
        return result

    def list_with_source(
        self,
        conditions=None,
        params=None,
        order_by="mi.collected_at DESC",
        page=1,
        page_size=20,
    ):
        placeholders = ", ".join(f"mi.{c}" for c in self.cols)
        where = ""
        if conditions:
            where = " WHERE " + " AND ".join(conditions)
        total = self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} mi{where}", params or []
        ).fetchone()[0]
        offset = (page - 1) * page_size
        rows = self.db.execute(
            f"SELECT {placeholders}, ms.name as source_name FROM {self.table_name} mi "
            f"LEFT JOIN market_intel_sources ms ON mi.source_id=ms.id"
            f"{where} ORDER BY {order_by} LIMIT ? OFFSET ?",
            (params or []) + [page_size, offset],
        ).fetchall()
        return total, [dict(r) for r in rows]

    def create_raw(self, data: dict) -> int:
        filtered = {k: v for k, v in data.items() if k in self.cols}
        if not filtered:
            return 0
        cols_str = ", ".join(filtered.keys())
        placeholders = ", ".join(["?"] * len(filtered))
        values = list(filtered.values())
        cursor = self.db.execute(
            f"INSERT INTO {self.table_name} ({cols_str}) VALUES ({placeholders})",
            values,
        )
        return cursor.lastrowid

    def delete_by_source(self, source_id: int):
        self.db.execute(
            f"DELETE FROM {self.table_name} WHERE source_id=?", (source_id,)
        )

    def update_fields(self, record_id: int, data: dict) -> bool:
        filtered = {k: v for k, v in data.items() if k in self.cols and k != "id"}
        if not filtered:
            return False
        set_clause = ", ".join(f"{k}=?" for k in filtered.keys())
        values = list(filtered.values()) + [record_id]
        cursor = self.db.execute(
            f"UPDATE {self.table_name} SET {set_clause} WHERE id=?", values
        )
        return cursor.rowcount > 0


class MarketIntelSourcesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "market_intel_sources", TABLE_MARKET_INTEL_SOURCES_COLS)

    def update_fields(self, record_id: int, data: dict) -> bool:
        filtered = {k: v for k, v in data.items() if k in self.cols and k != "id"}
        if not filtered:
            return False
        set_clause = ", ".join(f"{k}=?" for k in filtered.keys())
        values = list(filtered.values()) + [record_id]
        cursor = self.db.execute(
            f"UPDATE {self.table_name} SET {set_clause} WHERE id=?", values
        )
        self.db.commit()
        return cursor.rowcount > 0

    def list_active(self) -> list:
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE is_active=1"
        ).fetchall()
        return [dict(r) for r in rows]

    def count_active(self) -> int:
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE is_active=1"
        ).fetchone()[0]


class McpToolsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "mcp_tools", TABLE_MCP_TOOLS_COLS)

    def list_filtered(self, enabled=None) -> list:
        placeholders = ", ".join(self.cols)
        conditions, params = [], []
        if enabled is not None:
            conditions.append("enabled=?")
            params.append(enabled)
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name}{where} ORDER BY created_at DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def toggle_enabled(self, record_id: int) -> bool:
        from datetime import datetime

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = self.db.execute(
            f"UPDATE {self.table_name} SET enabled = NOT enabled, updated_at=? WHERE id=?",
            (now, record_id),
        )
        self.db.commit()
        return cursor.rowcount > 0

    def get_by_tool_name(self, tool_name: str):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE tool_name=?",
            (tool_name,),
        ).fetchone()
        return dict(row) if row else None


class MdtOpinionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "mdt_opinions", TABLE_MDT_OPINIONS_COLS)

    def list_by_session(self, session_id: int, round_number=None) -> list:
        placeholders = ", ".join(self.cols)
        conditions = ["session_id=?"]
        params = [session_id]
        if round_number is not None:
            conditions.append("round_number=?")
            params.append(round_number)
        where = "WHERE " + " AND ".join(conditions)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name}{where} ORDER BY round_number ASC, id ASC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def list_by_session_with_participant(self, session_id: int) -> list:
        placeholders = ", ".join(f"o.{c}" for c in self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders}, p.role_name, p.stance FROM {self.table_name} o "
            f"JOIN mdt_participants p ON p.id=o.participant_id "
            f"WHERE o.session_id=? ORDER BY o.round_number ASC, o.id ASC",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def avg_confidence(self) -> float:
        return self.db.execute(
            f"SELECT COALESCE(ROUND(AVG(confidence),2),0) FROM {self.table_name}"
        ).fetchone()[0]

    def build_round_summary(self, session_id: int, round_num: int) -> str:
        if round_num < 1:
            return ""
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders}, p.role_name FROM {self.table_name} o "
            f"JOIN mdt_participants p ON p.id=o.participant_id "
            f"WHERE o.session_id=? AND o.round_number=?",
            (session_id, round_num),
        ).fetchall()
        return "\n".join(
            f"- {r['role_name']}: {r['summary']}" for r in rows if r.get("summary")
        )

    def create_raw(self, data: dict) -> int:
        filtered = {k: v for k, v in data.items() if k in self.cols}
        if not filtered:
            return 0
        cols_str = ", ".join(filtered.keys())
        placeholders = ", ".join(["?"] * len(filtered))
        values = list(filtered.values())
        cursor = self.db.execute(
            f"INSERT INTO {self.table_name} ({cols_str}) VALUES ({placeholders})",
            values,
        )
        return cursor.lastrowid


class MdtParticipantsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "mdt_participants", TABLE_MDT_PARTICIPANTS_COLS)

    def list_by_session(self, session_id: int) -> list:
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE session_id=? ORDER BY id ASC",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def avg_per_session(self) -> float:
        return self.db.execute(
            "SELECT COALESCE(ROUND(AVG(c),2),0) FROM "
            f"(SELECT COUNT(*) c FROM {self.table_name} GROUP BY session_id)"
        ).fetchone()[0]

    def create_raw(self, data: dict) -> int:
        filtered = {k: v for k, v in data.items() if k in self.cols}
        if not filtered:
            return 0
        cols_str = ", ".join(filtered.keys())
        placeholders = ", ".join(["?"] * len(filtered))
        values = list(filtered.values())
        cursor = self.db.execute(
            f"INSERT INTO {self.table_name} ({cols_str}) VALUES ({placeholders})",
            values,
        )
        return cursor.lastrowid


class MdtSessionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "mdt_sessions", TABLE_MDT_SESSIONS_COLS)

    def count_by_field(self, field: str) -> dict:
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {field}, COUNT(*) as cnt FROM {self.table_name} GROUP BY {field}"
        ).fetchall()
        return {r[field]: r["cnt"] for r in rows}

    def count_completed(self) -> int:
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE status='completed'"
        ).fetchone()[0]

    def avg_field(self, field: str) -> float:
        return self.db.execute(
            f"SELECT COALESCE(ROUND(AVG({field}),2),0) FROM {self.table_name}"
        ).fetchone()[0]

    def list_recent(self, limit: int = 5) -> list:
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


class MemoryConsolidationLogRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(
            db, "memory_consolidation_log", TABLE_MEMORY_CONSOLIDATION_LOG_COLS
        )

    def list_recent(self, limit=5):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def count_by_type_since(self, consolidation_type, since):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} "
            "WHERE consolidation_type=? AND created_at >= ?",
            (consolidation_type, since),
        ).fetchone()[0]

    def trend_since(self, since):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT date(created_at) as day, consolidation_type, COUNT(*) as cnt "
            f"FROM {self.table_name} WHERE created_at >= ? "
            "GROUP BY date(created_at), consolidation_type ORDER BY day ASC",
            (since,),
        ).fetchall()
        return [dict(r) for r in rows]


class MemoryEntriesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "memory_entries", TABLE_MEMORY_ENTRIES_COLS)

    def list_active_ordered(self, order_by="importance DESC"):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} "
            f"WHERE is_active=1 ORDER BY {order_by}"
        ).fetchall()
        return [dict(r) for r in rows]

    def find_active_by_id(self, entry_id):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE id=? AND is_active=1",
            (entry_id,),
        ).fetchone()
        return dict(row) if row else None

    def find_by_source_active(self, source_type, source_id):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} "
            "WHERE source_type=? AND source_id=? AND is_active=1",
            (source_type, source_id),
        ).fetchone()
        return dict(row) if row else None

    def list_filtered(
        self, memory_type=None, importance_min=None, keyword=None, page=1, page_size=20
    ):
        conditions, params = ["is_active = 1"], []
        if memory_type:
            conditions.append("memory_type = ?")
            params.append(memory_type)
        if importance_min is not None:
            conditions.append("importance >= ?")
            params.append(importance_min)
        if keyword:
            conditions.append("(title LIKE ? OR content LIKE ?)")
            kw = f"%{keyword}%"
            params.extend([kw, kw])
        return self.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params,
            order_by="importance DESC",
        )

    def count_active(self):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE is_active=1"
        ).fetchone()[0]

    def by_type_stats(self):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT memory_type, COUNT(*) AS cnt, AVG(importance) AS avg_imp "
            f"FROM {self.table_name} WHERE is_active=1 GROUP BY memory_type"
        ).fetchall()
        return [dict(r) for r in rows]

    def all_context_tags_active(self):
        rows = self.db.execute(
            f"SELECT context_tags FROM {self.table_name} WHERE is_active=1"
        ).fetchall()
        return [dict(r) for r in rows]

    def increment_access(self, entry_id, now):
        self.db.execute(
            "UPDATE memory_entries SET access_count = access_count + 1, "
            "last_accessed = ? WHERE id = ?",
            (now, entry_id),
        )

    def find_similar_by_title(self, prefix, exclude_id, min_utility=0.8):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            "SELECT me2.id FROM memory_entries me2 "
            "JOIN memory_utility_scores mus2 ON me2.id=mus2.memory_entry_id "
            "WHERE me2.id!=? AND me2.is_active=1 AND me2.title LIKE ? "
            "AND mus2.utility_score >= ?",
            (exclude_id, prefix + "%", min_utility),
        ).fetchall()
        return [dict(r) for r in rows]

    def deactivate(self, entry_id, now):
        self.db.execute(
            "UPDATE memory_entries SET is_active=0, updated_at=? WHERE id=?",
            (now, entry_id),
        )

    def append_content(self, content片段, target_id, now):
        self.db.execute(
            "UPDATE memory_entries SET content=content || ? || ?, updated_at=? WHERE id=?",
            ("\n\n[MERGED] ", content片段, now, target_id),
        )

    def promote_importance(self, new_imp, entry_id, now):
        self.db.execute(
            "UPDATE memory_entries SET importance=?, updated_at=? WHERE id=?",
            (new_imp, now, entry_id),
        )


class MemoryGatesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "memory_gates", TABLE_MEMORY_GATES_COLS)

    def list_ordered(self):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]

    def find_active_by_source_type(self, source_type):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} "
            "WHERE source_type=? AND is_active=1",
            (source_type,),
        ).fetchone()
        return dict(row) if row else None


class MemoryRecallLogRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "memory_recall_log", TABLE_MEMORY_RECALL_LOG_COLS)

    def list_recent(self, limit=5):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


class MemoryUtilityScoresRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "memory_utility_scores", TABLE_MEMORY_UTILITY_SCORES_COLS)

    def upsert_score(self, data):
        filtered = {k: v for k, v in data.items() if k in self.cols}
        if not filtered:
            return
        cols_str = ", ".join(filtered.keys())
        placeholders = ", ".join(["?"] * len(filtered))
        self.db.execute(
            f"INSERT OR REPLACE INTO {self.table_name} ({cols_str}) VALUES ({placeholders})",
            list(filtered.values()),
        )

    def list_ranked(self, min_utility=0.0, limit=20):
        rows = self.db.execute(
            "SELECT me.id, me.title, me.memory_type, me.importance, me.access_count, "
            "me.last_accessed, mus.utility_score, mus.recency_score, mus.connectivity_score "
            "FROM memory_entries me JOIN memory_utility_scores mus ON me.id=mus.memory_entry_id "
            "WHERE mus.utility_score >= ? AND me.is_active=1 "
            "ORDER BY mus.utility_score DESC LIMIT ?",
            (min_utility, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def find_by_memory(self, memory_entry_id):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE memory_entry_id=?",
            (memory_entry_id,),
        ).fetchone()
        return dict(row) if row else None


class NmpaComplianceLogsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "nmpa_compliance_logs", TABLE_NMPA_COMPLIANCE_LOGS_COLS)

    def list_filtered(
        self, document_type=None, check_result=None, human_review_required=None
    ):
        conditions, params = [], []
        if document_type:
            conditions.append("document_type=?")
            params.append(document_type)
        if check_result:
            conditions.append("check_result=?")
            params.append(check_result)
        if human_review_required is not None:
            conditions.append("human_review_required=?")
            params.append(human_review_required)
        return self.list_all(
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )


class NodeMemoryLinksRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "node_memory_links", TABLE_NODE_MEMORY_LINKS_COLS)

    def count_by_node(self, node_id):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE node_id=?", (node_id,)
        ).fetchone()[0]

    def delete_by_node(self, node_id):
        self.db.execute(f"DELETE FROM {self.table_name} WHERE node_id=?", (node_id,))

    def delete_by_nodes(self, node_ids):
        if not node_ids:
            return
        ph = ",".join("?" for _ in node_ids)
        self.db.execute(
            f"DELETE FROM {self.table_name} WHERE node_id IN ({ph})", node_ids
        )

    def memory_ids_for_nodes(self, node_ids):
        if not node_ids:
            return []
        ph = ",".join("?" for _ in node_ids)
        rows = self.db.execute(
            f"SELECT DISTINCT me.id, me.title FROM memory_entries me "
            f"JOIN {self.table_name} nml ON me.id=nml.memory_entry_id "
            f"WHERE nml.node_id IN ({ph}) AND me.is_active=1",
            node_ids,
        ).fetchall()
        return [dict(r) for r in rows]

    def importance_for_nodes(self, node_ids):
        if not node_ids:
            return []
        ph = ",".join("?" for _ in node_ids)
        rows = self.db.execute(
            f"SELECT me.importance FROM memory_entries me "
            f"JOIN {self.table_name} nml ON me.id=nml.memory_entry_id "
            f"WHERE nml.node_id IN ({ph})",
            node_ids,
        ).fetchall()
        return [dict(r) for r in rows]

    def memory_entries_with_utility(self):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            "SELECT me.id, me.title, me.content, me.importance, me.access_count, "
            "me.last_accessed, me.is_active, mus.utility_score "
            "FROM memory_entries me "
            "JOIN memory_utility_scores mus ON me.id=mus.memory_entry_id "
            "WHERE me.is_active=1"
        ).fetchall()
        return [dict(r) for r in rows]


class NotificationTemplatesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(
            db, "notification_templates", TABLE_NOTIFICATION_TEMPLATES_COLS
        )


class NotificationsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "notifications", TABLE_NOTIFICATIONS_COLS)

    def create_notification(
        self,
        user_id: int,
        title: str,
        body_text: str,
        category: str,
        ref_type: str,
        ref_id: int,
    ):
        from datetime import datetime

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.create(
            {
                "user_id": user_id,
                "title": title,
                "body": body_text,
                "category": category,
                "ref_type": ref_type,
                "ref_id": ref_id,
                "created_at": now,
            }
        )


class OpportunitiesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "opportunities", TABLE_OPPORTUNITIES_COLS)


class OrchestrationTemplatesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(
            db, "orchestration_templates", TABLE_ORCHESTRATION_TEMPLATES_COLS
        )


class PipelineRunsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "pipeline_runs", TABLE_PIPELINE_RUNS_COLS)


class PipelineStepRunsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "pipeline_step_runs", TABLE_PIPELINE_STEP_RUNS_COLS)


class PipelineStepsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "pipeline_steps", TABLE_PIPELINE_STEPS_COLS)


class PrivacyBudgetsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "privacy_budgets", TABLE_PRIVACY_BUDGETS_COLS)


class PrivacyComputeJobsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "privacy_compute_jobs", TABLE_PRIVACY_COMPUTE_JOBS_COLS)


class RecommendationsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "recommendations", TABLE_RECOMMENDATIONS_COLS)

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]

    def count_clicked(self):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE clicked=1"
        ).fetchone()[0]

    def count_dismissed(self):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE dismissed=1"
        ).fetchone()[0]

    def count_by_rec_type(self):
        rows = self.db.execute(
            f"SELECT rec_type, COUNT(*) as cnt FROM {self.table_name} GROUP BY rec_type ORDER BY cnt DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def list_filtered(
        self,
        user_id=None,
        rec_type=None,
        clicked=None,
        dismissed=None,
        limit=50,
        offset=0,
    ):
        conditions, params = [], []
        if user_id is not None:
            conditions.append("user_id=?")
            params.append(user_id)
        if rec_type is not None:
            conditions.append("rec_type=?")
            params.append(rec_type)
        if clicked is not None:
            conditions.append("clicked=?")
            params.append(clicked)
        if dismissed is not None:
            conditions.append("dismissed=?")
            params.append(dismissed)
        return self.paginate(
            page=1,
            page_size=limit,
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )

    def mark_clicked(self, rec_id: int) -> bool:
        cursor = self.db.execute(
            f"UPDATE {self.table_name} SET clicked=1 WHERE id=?", (rec_id,)
        )
        self.db.commit()
        return cursor.rowcount > 0

    def mark_dismissed(self, rec_id: int) -> bool:
        cursor = self.db.execute(
            f"UPDATE {self.table_name} SET dismissed=1 WHERE id=?", (rec_id,)
        )
        self.db.commit()
        return cursor.rowcount > 0


class RouteLogsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "route_logs", TABLE_ROUTE_LOGS_COLS)

    def list_filtered(
        self,
        role_id=None,
        source=None,
        date_from=None,
        date_to=None,
        page=1,
        page_size=20,
    ):
        conditions, params = [], []
        if role_id is not None:
            conditions.append("assigned_role_id=?")
            params.append(role_id)
        if source is not None:
            conditions.append("source=?")
            params.append(source)
        if date_from:
            conditions.append("created_at>=?")
            params.append(date_from)
        if date_to:
            conditions.append("created_at<=?")
            params.append(date_to)
        return self.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )

    def role_distribution(self):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT assigned_role_id, assigned_role_name, COUNT(*) as cnt "
            f"FROM {self.table_name} GROUP BY assigned_role_id, assigned_role_name ORDER BY cnt DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def avg_latency(self):
        return self.db.execute(
            f"SELECT COALESCE(AVG(latency_ms), 0) FROM {self.table_name}"
        ).fetchone()[0]

    def list_recent(self, limit: int = 10):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


class RouteRulesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "route_rules", TABLE_ROUTE_RULES_COLS)

    def list_active_ordered(self):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE is_active=1 ORDER BY priority ASC"
        ).fetchall()
        return [dict(r) for r in rows]

    def list_all_ordered(self):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY priority ASC"
        ).fetchall()
        return [dict(r) for r in rows]


class RouteStatsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "route_stats", TABLE_ROUTE_STATS_COLS)

    def upsert(self, role_id: int, latency_ms: int, tokens: int, confidence: float):
        from datetime import datetime

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = self.db.execute(
            f"SELECT * FROM {self.table_name} WHERE role_id=?", (role_id,)
        ).fetchone()
        if row:
            total = row["total_routed"] + 1
            n = float(total)
            avg_confidence = round(
                (row["avg_confidence"] * (n - 1) + confidence) / n, 4
            )
            avg_tokens = round((row["avg_tokens"] * (n - 1) + tokens) / n, 2)
            avg_latency = round((row["avg_latency_ms"] * (n - 1) + latency_ms) / n, 2)
            self.db.execute(
                f"UPDATE {self.table_name} SET total_routed=?, avg_confidence=?, "
                "avg_tokens=?, avg_latency_ms=?, last_routed_at=?, updated_at=? WHERE role_id=?",
                (total, avg_confidence, avg_tokens, avg_latency, now, now, role_id),
            )
        else:
            self.db.execute(
                f"INSERT INTO {self.table_name} (role_id, total_routed, avg_confidence, "
                "avg_tokens, avg_latency_ms, last_routed_at, updated_at) VALUES (?,1,?,?,?,?,?)",
                (
                    role_id,
                    round(confidence, 4),
                    round(float(tokens), 2),
                    round(float(latency_ms), 2),
                    now,
                    now,
                ),
            )
        self.db.commit()

    def list_with_role_name(self):
        placeholders = ", ".join(f"rs.{c}" for c in self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders}, ar.name as role_name FROM {self.table_name} rs "
            "LEFT JOIN agent_roles ar ON rs.role_id=ar.id ORDER BY rs.total_routed DESC"
        ).fetchall()
        return [dict(r) for r in rows]


class SleepConsolidationLogsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(
            db, "sleep_consolidation_logs", TABLE_SLEEP_CONSOLIDATION_LOGS_COLS
        )

    def list_recent(self, limit=10):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


class SoapDecisionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "soap_decisions", TABLE_SOAP_DECISIONS_COLS)

    def list_active_filtered(
        self, status=None, priority=None, tag=None, page=1, page_size=20
    ):
        conditions = ["is_active=1"]
        params = []
        if status:
            conditions.append("status=?")
            params.append(status)
        if priority:
            conditions.append("priority=?")
            params.append(priority)
        if tag:
            conditions.append("tags LIKE ?")
            params.append(f"%{tag}%")
        return self.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params or None,
            order_by="created_at DESC",
        )

    def count_active(self):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE is_active=1"
        ).fetchone()[0]

    def count_by_status(self):
        rows = self.db.execute(
            f"SELECT status, COUNT(*) cnt FROM {self.table_name} WHERE is_active=1 GROUP BY status"
        ).fetchall()
        return {r["status"]: r["cnt"] for r in rows}

    def count_by_priority(self):
        rows = self.db.execute(
            f"SELECT priority, COUNT(*) cnt FROM {self.table_name} WHERE is_active=1 GROUP BY priority"
        ).fetchall()
        return {r["priority"]: r["cnt"] for r in rows}

    def list_active_recent(self, limit: int = 5):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE is_active=1 "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


class SoapTemplatesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "soap_templates", TABLE_SOAP_TEMPLATES_COLS)

    def list_active(self, category=None):
        conditions = ["is_active=1"]
        params = []
        if category:
            conditions.append("category=?")
            params.append(category)
        return self.list_all(
            conditions=conditions, params=params or None, order_by="id ASC"
        )


class TaskBoardsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "task_boards", TABLE_TASK_BOARDS_COLS)

    def get_active_by_id(self, board_id: int):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE id=? AND is_active=1",
            (board_id,),
        ).fetchone()
        return dict(row) if row else None


class TeamsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "teams", TABLE_TEAMS_COLS)


class TrainingAttributionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "training_attributions", TABLE_TRAINING_ATTRIBUTIONS_COLS)


class TrainingCorrectionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "training_corrections", TABLE_TRAINING_CORRECTIONS_COLS)


class TrainingModulesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "training_modules", TABLE_TRAINING_MODULES_COLS)


class TrainingRoiAnalysisRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "training_roi_analysis", TABLE_TRAINING_ROI_ANALYSIS_COLS)


class TrainingScriptsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "training_scripts", TABLE_TRAINING_SCRIPTS_COLS)


class TrainingSessionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "training_sessions", TABLE_TRAINING_SESSIONS_COLS)


class UserBehaviorsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "user_behaviors", TABLE_USER_BEHAVIORS_COLS)

    def count_by_user(self, user_id: int):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE user_id=?", (user_id,)
        ).fetchone()[0]

    def top_action_by_user(self, user_id: int):
        row = self.db.execute(
            f"SELECT action_type, COUNT(*) AS cnt FROM {self.table_name} "
            "WHERE user_id=? GROUP BY action_type ORDER BY cnt DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None

    def top_targets_by_user_action(
        self, user_id: int, action_type: str, limit: int = 5
    ):
        rows = self.db.execute(
            f"SELECT target_id, target_type, COUNT(*) AS cnt FROM {self.table_name} "
            "WHERE user_id=? AND action_type=? GROUP BY target_id, target_type "
            "ORDER BY cnt DESC LIMIT ?",
            (user_id, action_type, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_filtered(
        self, user_id=None, action_type=None, target_type=None, limit=50, offset=0
    ):
        conditions, params = [], []
        if user_id is not None:
            conditions.append("user_id=?")
            params.append(user_id)
        if action_type is not None:
            conditions.append("action_type=?")
            params.append(action_type)
        if target_type is not None:
            conditions.append("target_type=?")
            params.append(target_type)
        return self.paginate(
            page=1,
            page_size=limit,
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )

    def top_actions_global(self, limit: int = 10):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT action_type, COUNT(*) AS cnt FROM {self.table_name} "
            "GROUP BY action_type ORDER BY cnt DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


class UserProfilesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "user_profiles", TABLE_USER_PROFILES_COLS)

    def get_by_user_id(self, user_id: int):
        row = self.db.execute(
            f"SELECT {', '.join(self.cols)} FROM {self.table_name} WHERE user_id=?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None

    def upsert_profile(
        self,
        user_id: int,
        persona_type: str,
        specialization: str,
        experience_level: str,
        preferred_content_types: str,
        custom_tags: str,
    ):
        self.db.execute(
            f"INSERT INTO {self.table_name} (user_id, persona_type, specialization, experience_level, "
            "preferred_content_types, custom_tags, updated_at) "
            "VALUES (?,?,?,?,?,?,datetime('now')) "
            "ON CONFLICT(user_id) DO UPDATE SET persona_type=excluded.persona_type, "
            "specialization=excluded.specialization, experience_level=excluded.experience_level, "
            "preferred_content_types=excluded.preferred_content_types, "
            "custom_tags=excluded.custom_tags, updated_at=datetime('now')",
            (
                user_id,
                persona_type,
                specialization,
                experience_level,
                preferred_content_types,
                custom_tags,
            ),
        )
        self.db.commit()
        return self.get_by_user_id(user_id)


class UserTeamRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "user_team", TABLE_USER_TEAM_COLS)


class UsersRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "users", TABLE_USERS_COLS)

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]


class WorkingMemoryRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "working_memory", TABLE_WORKING_MEMORY_COLS)


class WorldTreeNodesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "world_tree_nodes", TABLE_WORLD_TREE_NODES_COLS)

    def exists_by_id(self, node_id):
        return (
            self.db.execute(
                f"SELECT id FROM {self.table_name} WHERE id=?", (node_id,)
            ).fetchone()
            is not None
        )

    def list_active_sorted(self):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} "
            "WHERE is_active=1 ORDER BY sort_order, name"
        ).fetchall()
        return [dict(r) for r in rows]

    def descendant_ids(self, node_id):
        ids, stack = [], [node_id]
        while stack:
            cur = stack.pop()
            ids.append(cur)
            stack.extend(
                c["id"]
                for c in self.db.execute(
                    f"SELECT id FROM {self.table_name} WHERE parent_id=?", (cur,)
                ).fetchall()
            )
        return ids

    def update_parent(self, node_id, parent_id, now):
        self.db.execute(
            f"UPDATE {self.table_name} SET parent_id=?, updated_at=? WHERE id=?",
            (parent_id, now, node_id),
        )

    def update_path(self, node_id, path, level, now):
        self.db.execute(
            f"UPDATE {self.table_name} SET path=?, level=?, updated_at=? WHERE id=?",
            (path, level, now, node_id),
        )

    def list_by_ids(self, node_ids):
        if not node_ids:
            return []
        ph = ",".join("?" for _ in node_ids)
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE id IN ({ph})",
            node_ids,
        ).fetchall()
        return [dict(r) for r in rows]


class WorldTreeSnapshotsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "world_tree_snapshots", TABLE_WORLD_TREE_SNAPSHOTS_COLS)

    def delete_by_node(self, node_id):
        self.db.execute(f"DELETE FROM {self.table_name} WHERE node_id=?", (node_id,))

    def delete_by_nodes(self, node_ids):
        if not node_ids:
            return
        ph = ",".join("?" for _ in node_ids)
        self.db.execute(
            f"DELETE FROM {self.table_name} WHERE node_id IN ({ph})", node_ids
        )
