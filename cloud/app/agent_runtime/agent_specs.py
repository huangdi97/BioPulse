"""Agent 规格定义，包含各 Agent 的角色描述、允许工具、迭代上限等配置。

@deprecated 使用 agents/*/identity.yaml 替代。保留用于 identity.yaml 未覆盖的 Agent 场景向后兼容。
"""

AGENT_SPECS = {
    "opportunity_scanner": {
        "role_desc": (
            "你是一个商机分析Agent，负责扫描招标信息、评估商机价值、推送高价值商机。"
            "你会用 query_bidding 查新招标，analyze_with_llm 评估匹配度，"
            "create_notification 推送结果。"
        ),
        "allowed_tools": ["query_bidding", "analyze_with_llm", "create_notification", "agent_brain_get", "agent_brain_set"],
        "max_iterations": 8,
        "default_temperature": 0.3,
        "max_permission": "write",
        "trigger_cron": None,
    },
    "sales_coach_analyst": {
        "role_desc": (
            "你是一个销售教练分析Agent，负责分析销售训练数据、识别能力弱点、生成个性化训练建议。"
            "你会用 query_training_records 拉训练数据，analyze_with_llm 分析模式，"
            "create_notification 推送推荐。"
        ),
        "allowed_tools": [
            "query_training_records",
            "analyze_with_llm",
            "create_notification",
            "write_memory",
            "agent_brain_get",
            "agent_brain_set",
        ],
        "max_iterations": 10,
        "default_temperature": 0.4,
        "max_permission": "write",
        "trigger_cron": None,
        "output_schema": {
            "type": "object",
            "properties": {
                "weakness_areas": {"type": "array", "items": {"type": "string"}},
                "overall_score": {"type": "number", "minimum": 0, "maximum": 100},
                "recommendations": {"type": "array", "items": {"type": "string"}},
                "priority_level": {"type": "string", "enum": ["low", "medium", "high"]},
            },
            "required": ["weakness_areas", "overall_score", "recommendations"],
        },
    },
    "knowledge_worker": {
        "role_desc": ("你是一个知识维护Agent，负责在企业知识图谱中维护关联关系。新信息进来时，你会搜索相关知识、建立关联、记录发现。"),
        "allowed_tools": [
            "query_knowledge_graph",
            "analyze_with_llm",
            "write_memory",
            "search_memory",
            "agent_brain_get",
        ],
        "max_iterations": 6,
        "default_temperature": 0.3,
        "max_permission": "read",
        "trigger_cron": None,
    },
    "compliance_monitor": {
        "role_desc": (
            "你是一个合规监控Agent，负责费用、拜访、流向三角勾稽交叉验证，通过L4循环执行。"
            "你会用 verify_expense、verify_visit、trace_distribution 收集证据，"
            "调用 triangulation_check 进行跨维度判定，必要时 trigger_red_light，"
            "并用 write_audit_log 写入审计链。"
            "所有步骤通过planner生成计划→executor执行→verifier校验→analyzer+reflector容错。"
        ),
        "allowed_tools": [
            "verify_expense",
            "verify_visit",
            "trace_distribution",
            "triangulation_check",
            "trigger_red_light",
            "write_audit_log",
        ],
        "max_iterations": 5,
        "max_retries": 3,
        "default_temperature": 0.2,
        "max_permission": "write",
        "trigger_cron": None,
        "trigger_mode": "l4",
        "trigger_plan_steps": [
            {"step": 1, "tool": "verify_expense", "description": "核查费用"},
            {"step": 2, "tool": "verify_visit", "description": "核查拜访"},
            {"step": 3, "tool": "trace_distribution", "description": "追踪流向"},
            {"step": 4, "tool": "triangulation_check", "description": "三角勾稽交叉验证"},
            {"step": 5, "tool": "complete", "description": "输出结论"},
        ],
        "output_schema": {
            "type": "object",
            "properties": {
                "decision": {"type": "string", "enum": ["pass", "flag", "red_light"]},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "patterns_detected": {"type": "array", "items": {"type": "string"}},
                "recommendation": {"type": "string"},
            },
            "required": ["decision", "confidence", "patterns_detected"],
        },
    },
    "sales_suggestion": {
        "role_desc": (
            "你是一个销售策略建议Agent，负责在拜访完成后进行多步信息收集、因果推断、"
            "多方案策略推荐与Pre-call Brief生成。你会用 query_hcp_profile、"
            "query_visit_history、query_competitor_intel、run_causal_attribution 收集证据，"
            "并调用 generate_brief 输出结构化销售建议。"
        ),
        "allowed_tools": [
            "query_hcp_profile",
            "query_visit_history",
            "query_competitor_intel",
            "run_causal_attribution",
            "generate_brief",
        ],
        "max_iterations": 10,
        "max_retries": 3,
        "default_temperature": 0.3,
        "max_permission": "write",
        "trigger_cron": None,
        "event_subscriptions": ["visit.completed", "visit_completion", "拜访完成事件"],
        "output_schema": {
            "type": "object",
            "properties": {
                "strategy_type": {"type": "string", "enum": ["brief", "deep_dive", "competitive", "general"]},
                "key_findings": {"type": "array", "items": {"type": "string"}},
                "recommended_actions": {"type": "array", "items": {"type": "string"}},
                "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
            },
            "required": ["strategy_type", "key_findings", "recommended_actions"],
        },
    },
    "competitor_crawler": {
        "role_desc": (
            "你是一个竞品爬虫Agent，负责抓取竞品情报数据。"
            "你会用 crawler_start 启动抓取任务，crawler_stop 停止指定源的抓取，"
            "crawler_query 查询已抓取的数据。"
        ),
        "allowed_tools": ["crawler_start", "crawler_stop", "crawler_query"],
        "max_iterations": 20,
        "max_retries": 3,
        "default_temperature": 0.3,
        "max_permission": "write",
        "trigger_cron": None,
        "type": "functional",
    },
    "anomaly_analysis": {
        "role": "异常分析Agent",
        "role_desc": (
            "你是一个异常分析Agent，负责订阅合规红灯事件，执行假设生成、证据验证、"
            "模式发现、因果推断和自然语言根因叙事。你会先用 collect_related_data 收集证据，"
            "再用 run_pattern_analysis 和 discover_related_patterns 检查跨代表模式，"
            "用 run_causal_inference 收敛根因，最后调用 generate_narrative 输出总裁可读报告。"
        ),
        "tools": [
            "collect_related_data",
            "run_pattern_analysis",
            "run_causal_inference",
            "generate_narrative",
            "discover_related_patterns",
        ],
        "allowed_tools": [
            "collect_related_data",
            "run_pattern_analysis",
            "run_causal_inference",
            "generate_narrative",
            "discover_related_patterns",
        ],
        "max_iterations": 15,
        "max_retries": 3,
        "execution_config": {"max_steps": 15, "max_retries": 3},
        "default_temperature": 0.2,
        "max_permission": "read",
        "trigger_cron": None,
        "edac_subscriptions": [
            {
                "source_agent": "compliance_monitor",
                "event_type": "compliance.red_light.triggered",
                "handler": "anomaly_analysis",
            }
        ],
        "event_subscriptions": [
            "compliance.red_light",
            "compliance.red_light.triggered",
            "red_light.triggered",
            "合规红灯事件",
        ],
        "output_schema": {
            "type": "object",
            "properties": {
                "root_cause": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "related_patterns": {"type": "array", "items": {"type": "string"}},
                "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                "recommended_action": {"type": "string"},
            },
            "required": ["root_cause", "confidence", "severity"],
        },
    },
}
