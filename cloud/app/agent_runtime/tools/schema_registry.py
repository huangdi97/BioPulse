"""Schema Registry — Agent 可见的数据实体关系图谱。

让 Agent "理解"整个后端的数据结构：哪些实体、哪些关系、哪些可查。
GraphQL 式类型化后端接口，替代盲调用。
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SchemaRegistry:
    def __init__(self):
        self._entities: dict[str, dict[str, Any]] = {}
        self._relations: list[dict[str, str]] = []
        self._register_defaults()

    def _register_defaults(self):
        entities = [
            {
                "name": "HCP",
                "fields": ["id", "name", "specialty", "region", "affiliation", "prescription_volume"],
                "description": "Healthcare professional / 医生",
            },
            {
                "name": "Visit",
                "fields": ["id", "hcp_id", "date", "purpose", "outcome", "next_visit_date"],
                "description": "拜访记录",
            },
            {
                "name": "ComplianceEvent",
                "fields": ["id", "hcp_id", "event_type", "severity", "description", "resolved", "date"],
                "description": "合规事件",
            },
            {
                "name": "ExpenseReport",
                "fields": ["id", "hcp_id", "amount", "category", "status", "date"],
                "description": "费用报告",
            },
            {
                "name": "CompetitorDrug",
                "fields": ["id", "drug_name", "company", "approved_indications", "market_share", "status"],
                "description": "竞品药物",
            },
            {
                "name": "Opportunity",
                "fields": ["id", "hcp_id", "type", "value", "stage", "assigned_to"],
                "description": "销售机会",
            },
            {
                "name": "Region",
                "fields": ["id", "name", "manager", "budget"],
                "description": "区域",
            },
        ]
        for e in entities:
            self._entities[e["name"]] = {"fields": e["fields"], "description": e["description"]}

        relations = [
            ("HCP", "Visit", "has_visit", "HCP → Visit: 一个医生有多次拜访"),
            ("HCP", "ExpenseReport", "has_expense", "HCP → ExpenseReport: 一个医生有多次费用报告"),
            ("HCP", "Opportunity", "has_opportunity", "HCP → Opportunity: 一个医生有多个销售机会"),
            ("HCP", "ComplianceEvent", "has_compliance", "HCP → ComplianceEvent: 一个医生可能有多个合规事件"),
            ("CompetitorDrug", "HCP", "prescribed_by", "CompetitorDrug → HCP: 竞品药物被医生处方"),
            ("Region", "HCP", "located_in", "Region → HCP: 区域包含医生"),
            ("Region", "ComplianceEvent", "reported_in", "Region → ComplianceEvent: 区域内有合规事件"),
            ("Region", "Opportunity", "opportunity_in", "Region → Opportunity: 区域内有销售机会"),
        ]
        for src, tgt, rel, desc in relations:
            self._relations.append({"source": src, "target": tgt, "relation": rel, "description": desc})

    def register_entity(self, entity_name: str, fields: list[str], relations: list[dict[str, str]] | None = None, description: str = ""):
        if entity_name in self._entities:
            logger.warning("Entity '%s' already registered, overwriting", entity_name)
        self._entities[entity_name] = {"fields": fields, "description": description}
        if relations:
            for r in relations:
                self._relations.append(
                    {
                        "source": entity_name,
                        "target": r["target"],
                        "relation": r.get("relation", "related_to"),
                        "description": r.get("description", ""),
                    }
                )
        logger.info("Registered entity: %s with %d fields", entity_name, len(fields))

    def get_entity_graph(self) -> dict[str, Any]:
        return {
            "entities": {name: info["fields"] for name, info in self._entities.items()},
            "relations": [
                {
                    "source": r["source"],
                    "target": r["target"],
                    "relation": r["relation"],
                    "description": r["description"],
                }
                for r in self._relations
            ],
        }

    def suggest_query_path(self, from_entity: str, to_entity: str, goal: str = "") -> list[dict[str, str]]:
        results = []
        for r in self._relations:
            if r["source"] == from_entity and r["target"] == to_entity:
                entry = {"path": f"{from_entity} → {to_entity}", "via": r["relation"], "description": r["description"]}
                results.append(entry)
        for r in self._relations:
            if r["source"] == to_entity and r["target"] == from_entity:
                entry = {"path": f"{from_entity} ← {to_entity}", "via": r["relation"], "description": r["description"]}
                results.append(entry)
        if not results:
            indirect = []
            for r1 in self._relations:
                if r1["source"] == from_entity:
                    for r2 in self._relations:
                        if r2["source"] == r1["target"] and r2["target"] == to_entity:
                            indirect.append(
                                {
                                    "path": f"{from_entity} → {r1['target']} → {to_entity}",
                                    "via": f"{r1['relation']} + {r2['relation']}",
                                    "description": f"通过 {r1['target']} 间接关联",
                                }
                            )
            results = indirect
        return results


_schema_registry: SchemaRegistry | None = None


def get_schema_registry() -> SchemaRegistry:
    global _schema_registry
    if _schema_registry is None:
        _schema_registry = SchemaRegistry()
    return _schema_registry
