"""归因分配模块，提供因子元信息与日期工具函数。"""

from datetime import datetime, timedelta, timezone

_FACTOR_META = [
    {
        "name": "visit_frequency",
        "display_name": "拜访频率",
        "max_score": 35,
        "description": "近30天客户拜访次数。>5次给30-35分，3-5次给20-29分，1-2次给5-19分，0次给0分",
    },
    {
        "name": "product_match",
        "display_name": "产品匹配度",
        "max_score": 25,
        "description": "商机阶段匹配度。negotiation/won给20-25分，proposal给10-19分，lead/qualify给0-9分",
    },
    {
        "name": "hcp_relation",
        "display_name": "HCP关系强度",
        "max_score": 20,
        "description": "近60天与该客户关联的正面交互占比*20",
    },
    {
        "name": "competitor_threat",
        "display_name": "竞品活动",
        "max_score": 15,
        "description": "竞品活动记录扣分，最多-15分",
    },
    {
        "name": "time_window",
        "display_name": "时间窗口",
        "max_score": 10,
        "description": "距close_date<30天给8-10分，30-60天给4-7分，>60天或空给0分",
    },
    {
        "name": "stage_weight",
        "display_name": "阶段权重",
        "max_score": 10,
        "description": "won=10, negotiation=8, proposal=6, qualify=3, lead=1, lost=0",
    },
]

_STAGE_WEIGHTS = {
    "won": 10,
    "closed_won": 10,
    "negotiation": 8,
    "proposal": 6,
    "qualify": 3,
    "qualification": 3,
    "lead": 1,
    "lost": 0,
    "closed_lost": 0,
}

_RECOMMENDATIONS = {
    "visit_frequency": "建议增加HCP拜访频次，提升商机推进速度。",
    "product_match": "产品匹配度处于高位，建议加快商务谈判进程。",
    "hcp_relation": "HCP关系是当前最强驱动因子，建议维持并深化合作关系。",
    "competitor_threat": "竞品活动活跃，建议加强差异化价值传递并密切关注竞品动向。",
    "time_window": "时间窗口紧迫，建议优先处理该商机的关键决策节点。",
    "stage_weight": "商机阶段权重较高，建议保持当前推进节奏。",
}


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _days_ago(n: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=n)).strftime("%Y-%m-%d")


def _calc_month_days(close_date: str) -> int:
    try:
        clean = close_date.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (dt - datetime.now(timezone.utc)).days
    except (ValueError, TypeError):
        return -1
