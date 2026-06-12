"""知识图谱服务，负责实体与关系的创建、查询与图搜索。"""

import hashlib
import json
import uuid

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    KgEntitiesRepository,
    KgRelationsRepository,
    KgSearchCacheRepository,
)
from shared.base_service import BaseService


def _bfs_expand(
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
        frontier = next_frontier
    return ent_dict, rel_dict


class KgService(BaseService):
    """知识图谱服务，提供知识图谱的实体管理、关系管理与图搜索功能。"""

    def create_entity(self, data, user: dict) -> dict:
        """创建知识图谱实体。

        Args:
            data: 实体创建数据。
            user: 用户信息字典。

        Returns:
            新创建的实体字典。

        Raises:
            HTTPException 409: 实体 ID 已存在。
        """
        entities_repo = KgEntitiesRepository(self._connection())
        entity_id = data.entity_id or f"kg:{data.entity_type}:{uuid.uuid4()}"
        if entities_repo.exists_entity_id(entity_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Entity ID already exists")
        entities_repo.create(
            {
                "entity_id": entity_id,
                "entity_type": data.entity_type,
                "name": data.name,
                "aliases": json.dumps(data.aliases, ensure_ascii=False),
                "properties": json.dumps(data.properties, ensure_ascii=False),
                "source_table": data.source_table,
                "source_row_id": data.source_row_id or 0,
                "confidence": data.confidence,
                "created_by": int(user["sub"]),
            }
        )
        return entities_repo.get_by_entity_id(entity_id)

    def list_entities(self, entity_type=None, name=None, status_="active") -> list:
        """查询实体列表，支持按类型、名称和状态筛选。

        Args:
            entity_type: 实体类型筛选。
            name: 实体名称筛选。
            status_: 实体状态筛选，默认 "active"。

        Returns:
            实体字典列表。
        """
        entities_repo = KgEntitiesRepository(self._connection())
        return entities_repo.list_filtered(entity_type=entity_type, name=name, status_=status_)

    def get_entity(self, entity_id: str) -> dict:
        """根据 ID 获取实体及其关联关系。

        Args:
            entity_id: 实体 ID。

        Returns:
            包含实体和关系列表的字典。

        Raises:
            HTTPException 404: 实体不存在。
        """
        entities_repo = KgEntitiesRepository(self._connection())
        relations_repo = KgRelationsRepository(self._connection())
        row = entities_repo.get_by_entity_id(entity_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
        rels = relations_repo.list_by_entity_id(entity_id)
        return {"entity": row, "relations": rels}

    def delete_entity(self, entity_id: str) -> dict:
        """软删除指定实体。

        Args:
            entity_id: 实体 ID。

        Returns:
            包含实体 ID 和状态的字典。

        Raises:
            HTTPException 404: 实体不存在。
        """
        entities_repo = KgEntitiesRepository(self._connection())
        if not entities_repo.exists_entity_id(entity_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
        entities_repo.soft_delete_by_entity_id(entity_id)
        return {"entity_id": entity_id, "status": "inactive"}

    def create_relation(self, data) -> dict:
        """创建实体间的关系。

        Args:
            data: 关系创建数据。

        Returns:
            新创建的关系字典。

        Raises:
            HTTPException 404: 源或目标实体不存在。
        """
        entities_repo = KgEntitiesRepository(self._connection())
        relations_repo = KgRelationsRepository(self._connection())
        for label, eid in [
            ("Source", data.source_entity_id),
            ("Target", data.target_entity_id),
        ]:
            entity = entities_repo.get_by_entity_id(eid)
            if not entity or entity.get("status") != "active":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{label} entity not found",
                )
        row_id = relations_repo.create(
            {
                "source_entity_id": data.source_entity_id,
                "target_entity_id": data.target_entity_id,
                "relation_type": data.relation_type,
                "weight": data.weight,
                "properties": json.dumps(data.properties, ensure_ascii=False),
                "direction": data.direction,
                "confidence": data.confidence,
            }
        )
        return relations_repo.get_by_id(row_id)

    def list_relations(self, source=None, target=None, relation_type=None) -> list:
        """查询关系列表，支持按源实体、目标实体和关系类型筛选。

        Args:
            source: 源实体 ID 筛选。
            target: 目标实体 ID 筛选。
            relation_type: 关系类型筛选。

        Returns:
            关系字典列表。
        """
        relations_repo = KgRelationsRepository(self._connection())
        return relations_repo.list_filtered(source=source, target=target, relation_type=relation_type)

    def delete_relation(self, relation_id: int) -> dict:
        """删除指定关系。

        Args:
            relation_id: 关系 ID。

        Returns:
            包含关系 ID 和删除状态的字典。

        Raises:
            HTTPException 404: 关系不存在。
        """
        relations_repo = KgRelationsRepository(self._connection())
        if not relations_repo.get_by_id(relation_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relation not found")
        relations_repo.delete(relation_id)
        return {"relation_id": relation_id, "deleted": True}

    def search_kg(self, data) -> dict:
        """搜索知识图谱，基于查询文本进行 BFS 扩展。

        Args:
            data: 搜索参数（包含 query、entity_types、max_depth、limit 等）。

        Returns:
            包含实体和关系列表的字典。
        """
        entities_repo = KgEntitiesRepository(self._connection())
        relations_repo = KgRelationsRepository(self._connection())
        cache_repo = KgSearchCacheRepository(self._connection())
        seeds = [r["entity_id"] for r in entities_repo.search_by_name_and_types(data.query, entity_types=data.entity_types, limit=data.limit)]
        ent_dict, rel_dict = _bfs_expand(entities_repo, relations_repo, seeds, data.max_depth)
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

    def get_subgraph(self, entity_id: str, max_depth: int = 2) -> dict:
        """获取指定实体的子图（BFS 扩展）。

        Args:
            entity_id: 中心实体 ID。
            max_depth: 最大扩展深度，默认 2。

        Returns:
            包含实体和关系列表的字典。

        Raises:
            HTTPException 404: 实体不存在。
        """
        entities_repo = KgEntitiesRepository(self._connection())
        relations_repo = KgRelationsRepository(self._connection())
        entity = entities_repo.get_by_entity_id(entity_id)
        if not entity or entity.get("status") != "active":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
        ent_dict, rel_dict = _bfs_expand(entities_repo, relations_repo, [entity_id], max_depth)
        return {
            "entities": list(ent_dict.values()),
            "relations": list(rel_dict.values()),
        }

    def dashboard(self) -> dict:
        """获取知识图谱仪表盘统计数据。

        Returns:
            包含各类统计数据的字典。
        """
        entities_repo = KgEntitiesRepository(self._connection())
        relations_repo = KgRelationsRepository(self._connection())
        return {
            "total_entities": entities_repo.count_active(),
            "total_relations": relations_repo.count_all(),
            "entity_types": entities_repo.count_by_entity_type(),
            "relation_types": relations_repo.count_by_relation_type(),
            "top_connected": relations_repo.top_connected(limit=10),
        }
