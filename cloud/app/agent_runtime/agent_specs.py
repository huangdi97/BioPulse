"""Agent 规格定义，包含各 Agent 的角色描述、允许工具、迭代上限等配置。"""

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
}
