import sqlite3


def seed_rl_routing(conn: sqlite3.Connection) -> None:
    """count = conn.execute("SELECT COUNT(*) FROM routing_strategies").fetchone()[0]"""
    if count > 0:
        return

    strategies = [
        ("compliance_default", "合规默认路由", "合规相关任务路由到合规引擎", "compliance_%", "compliance_engine", 10),
        ("research_default", "科研默认路由", "科研任务路由到PI", "research_%", "research_pi", 20),
        ("customer_support", "客户支持路由", "支持类任务路由到客服", "support_%", "customer_service", 30),
        ("data_analysis", "数据分析路由", "分析类任务路由到分析师", "analysis_%", "data_analyst", 40),
        ("general_fallback", "通用兜底路由", "未匹配任何规则的任务", "%", "general_agent", 999),
    ]
    for key, name, desc, pattern, route_to, priority in strategies:
        conn.execute(
            "INSERT INTO routing_strategies "
            "(strategy_key, name, description, task_type_pattern, route_to, priority) "
            "VALUES (?,?,?,?,?,?)",
            (key, name, desc, pattern, route_to, priority),
        )

    log_count = conn.execute("SELECT COUNT(*) FROM routing_log").fetchone()[0]
    if log_count > 0:
        conn.commit()
        return

    logs = [
        ("T001", "compliance_check", "api", "compliance_default", "compliance_engine", 120, 1),
        ("T002", "compliance_review", "api", "compliance_default", "compliance_engine", 200, 1),
        ("T003", "research_query", "web", "research_default", "research_pi", 350, 1),
        ("T004", "support_ticket", "web", "customer_support", "customer_service", 80, 1),
        ("T005", "analysis_report", "api", "data_analysis", "data_analyst", 500, 0),
        ("T006", "compliance_audit", "web", "compliance_default", "compliance_engine", 150, 1),
        ("T007", "support_escalation", "api", "customer_support", "customer_service", 90, 1),
        ("T008", "research_match", "web", "research_default", "research_pi", 410, 0),
        ("T009", "analysis_dashboard", "api", "data_analysis", "data_analyst", 300, 1),
        ("T010", "general_help", "web", "general_fallback", "general_agent", 60, 1),
    ]
    for task_id, task_type, source, strategy, routed_to, duration, success in logs:
        conn.execute(
            "INSERT INTO routing_log "
            "(task_id, task_type, source, strategy_used, routed_to, duration_ms, success) "
            "VALUES (?,?,?,?,?,?,?)",
            (task_id, task_type, source, strategy, routed_to, duration, success),
        )
    conn.commit()
