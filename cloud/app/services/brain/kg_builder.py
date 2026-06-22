"""图谱构建逻辑：BFS 扩展与三元组处理。"""

import hashlib
import json

from cloud.app.repositories import (
    KgEntitiesRepository,
    KgRelationsRepository,
    KgSearchCacheRepository,
)


def _process_relation_batch(rels: list, visited_relations: set, visited_entities: set, rel_dict: dict, ent_dict: dict, entities_repo) -> set:
    next_frontier: set = set()
    for r in rels:
        rid = r["id"]
        if rid not in visited_relations:
            visited_relations.add(rid)
            rel_dict[str(rid)] = r
        for side in (r["source_entity_id"], r["target_entity_id"]):
            if side not in visited_entities:
                visited_entities.add(side)
                next_frontier.add(side)
                er = entities_repo.get_by_entity_id(side)
                if er and er.get("status") == "active":
                    ent_dict[side] = er
    return next_frontier


def bfs_expand(
    entities_repo: KgEntitiesRepository,
    relations_repo: KgRelationsRepository,
    seed_eids,
    max_depth,
):
    """使用 BFS 算法扩展知识图谱中的实体与关系。

    Args:
        entities_repo: 实体仓库对象。
        relations_repo: 关系仓库对象。
        seed_eids: 起始实体 ID 集合。
        max_depth: 最大遍历深度。

    Returns:
        (实体字典, 关系字典) 的元组。
    """
    visited_entities: set = set()
    visited_relations: set = set()
    ent_dict: dict = {}
    rel_dict: dict = {}

    for eid in seed_eids:
        row = entities_repo.get_by_entity_id(eid)
        if row and row.get("status") == "active":
            visited_entities.add(eid)
            ent_dict[eid] = row

    frontier = set(visited_entities)
    for _ in range(max_depth):
        if not frontier:
            break
        next_frontier: set = set()
        f_list = list(frontier)
        for bs in range(0, len(f_list), 500):
            batch = f_list[bs : bs + 500]
            rels = relations_repo.list_by_entity_ids_batch(batch)
            nf = _process_relation_batch(rels, visited_relations, visited_entities, rel_dict, ent_dict, entities_repo)
            next_frontier.update(nf)
        frontier = next_frontier
    return ent_dict, rel_dict


def search_kg(
    entities_repo: KgEntitiesRepository,
    relations_repo: KgRelationsRepository,
    cache_repo: KgSearchCacheRepository,
    data,
):
    """搜索知识图谱，基于查询文本进行 BFS 扩展。"""
    seeds = [r["entity_id"] for r in entities_repo.search_by_name_and_types(data.query, entity_types=data.entity_types, limit=data.limit)]
    ent_dict, rel_dict = bfs_expand(entities_repo, relations_repo, seeds, data.max_depth)
    qhash = hashlib.md5(json.dumps(data.model_dump(), sort_keys=True).encode()).hexdigest()
    cache_repo.create(
        {
            "query_hash": qhash,
            "query_text": data.query,
            "result_summary": json.dumps(
                {"entities": len(ent_dict), "relations": len(rel_dict)},
                ensure_ascii=False,
            ),
            "result_count": len(ent_dict) + len(rel_dict),
        }
    )
    return {
        "entities": list(ent_dict.values()),
        "relations": list(rel_dict.values()),
    }


def get_subgraph(
    entities_repo: KgEntitiesRepository,
    relations_repo: KgRelationsRepository,
    entity_id: str,
    max_depth: int = 2,
):
    """获取指定实体的子图（BFS 扩展）。"""
    ent_dict, rel_dict = bfs_expand(entities_repo, relations_repo, [entity_id], max_depth)
    return {
        "entities": list(ent_dict.values()),
        "relations": list(rel_dict.values()),
    }
