"""知识图谱统计与聚合函数。"""

from cloud.app.repositories import (
    KgEntitiesRepository,
    KgRelationsRepository,
)


def dashboard_stats(
    entities_repo: KgEntitiesRepository,
    relations_repo: KgRelationsRepository,
) -> dict:
    """获取知识图谱仪表盘统计数据。"""
    return {
        "total_entities": entities_repo.count_active(),
        "total_relations": relations_repo.count_all(),
        "entity_types": entities_repo.count_by_entity_type(),
        "relation_types": relations_repo.count_by_relation_type(),
        "top_connected": relations_repo.top_connected(limit=10),
    }
