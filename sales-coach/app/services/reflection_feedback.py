"""反思反馈模块，根据评分结果生成改进建议并推荐训练场景。"""

from typing import Optional


def _generate_improvements(scores: dict, strengths_weaknesses: Optional[dict] = None) -> list:
    suggestions = []
    priority = 1

    thresholds = [
        ("compliance", "加强合规意识培训，熟记合规检查清单", 70),
        ("product_knowledge", "建议深入学习产品知识手册，增加产品培训频次", 65),
        ("communication", "提升沟通技巧，建议参加沟通表达专项训练", 60),
        ("objection_handling", "加强异议处理演练，模拟更多客户异议场景", 55),
    ]

    for dim, suggestion, threshold in thresholds:
        if scores.get(dim, 100) < threshold:
            suggestions.append(
                {
                    "priority": priority,
                    "dimension": dim,
                    "suggestion": suggestion,
                }
            )
            priority += 1

    if not suggestions:
        suggestions.append(
            {
                "priority": 1,
                "dimension": "overall",
                "suggestion": "整体表现良好，建议保持并挑战更高难度的场景",
            }
        )

    if strengths_weaknesses and strengths_weaknesses.get("weaknesses"):
        for w in strengths_weaknesses["weaknesses"]:
            suggestions.append(
                {
                    "priority": priority,
                    "dimension": "custom",
                    "suggestion": f"针对弱项「{w}」制定专项提升计划",
                }
            )
            priority += 1

    return suggestions


def _recommend_scenarios(scores: dict, weaknesses: list) -> list:
    recommended = []
    if scores.get("compliance", 100) < 80:
        recommended.append("合规话术专项训练")
    if scores.get("objection_handling", 100) < 70:
        recommended.append("异议处理强化场景")
    if scores.get("communication", 100) < 70:
        recommended.append("沟通技巧进阶练习")
    if scores.get("product_knowledge", 100) < 70:
        recommended.append("产品知识问答实战")
    if not recommended:
        recommended.append("高级综合销售场景")
    return recommended
