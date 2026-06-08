"""场景模拟器模块，基于知识图谱实体动态生成训练场景。"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from typing import List

from sales_coach.app.scenario_db import _read_kg_entities

logger = logging.getLogger(__name__)


class ScenarioSimulator:
    def generate_training_scenarios(self) -> List[dict]:
        entities = _read_kg_entities(["drug", "disease"])
        if not entities:
            return []

        now = datetime.now(timezone.utc).isoformat()
        scenarios = []
        templates = []

        for e in entities:
            etype = e["entity_type"]
            name = e["name"]
            props = {}
            try:
                props = json.loads(e["properties"] or "{}")
            except (json.JSONDecodeError, TypeError):
                logger.warning("Failed to parse knowledge graph entity properties", exc_info=True)

            if etype == "drug":
                category = props.get("category", "药品知识")
                templates.append(
                    {
                        "title": f"产品知识：{name}的临床应用",
                        "role_setting": f"你是一名医药代表，正在向医生介绍{name}",
                        "goal": f"让医生充分了解{name}的临床价值和适用范围",
                        "difficulty": "medium",
                        "category": "drug",
                        "content": f"请详细介绍{name}（{category}）的核心临床数据、适用患者人群及安全性信息。",
                        "tips": f"重点突出{name}的差异化优势，避免绝对化表述。",
                    }
                )
            elif etype == "disease":
                prevalence = props.get("prevalence", "")
                desc_suffix = f"（{prevalence}流行病学数据）" if prevalence else ""
                templates.append(
                    {
                        "title": f"疾病教育：{name}的诊疗沟通",
                        "role_setting": f"你是一名医学信息顾问，需要向医生提供{name}的学术支持",
                        "goal": f"通过提供{name}的权威诊疗信息建立学术信任",
                        "difficulty": "medium",
                        "category": "disease",
                        "content": f"请向医生介绍{name}{desc_suffix}的最新诊疗指南和临床研究进展。",
                        "tips": "使用循证医学证据，引用权威指南，展示专业价值。",
                    }
                )

        templates = templates[:5]
        for t in templates:
            t["created_at"] = now
            t["updated_at"] = now
            t["is_active"] = 1
            scenarios.append(t)

        return scenarios

    def append_scenarios_to_db(self, conn: sqlite3.Connection, scenarios: List[dict], created_by: int = 1) -> int:
        count = 0
        for sc in scenarios:
            conn.execute(
                "INSERT INTO coach_scenario (title, role_setting, goal, difficulty, "
                "category, content, tips, is_active, created_by, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    sc["title"],
                    sc["role_setting"],
                    sc["goal"],
                    sc["difficulty"],
                    sc["category"],
                    sc["content"],
                    sc["tips"],
                    sc["is_active"],
                    created_by,
                    sc["created_at"],
                    sc["updated_at"],
                ),
            )
            count += 1
        conn.commit()
        return count
