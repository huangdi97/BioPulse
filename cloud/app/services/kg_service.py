"""知识图谱服务，负责实体与关系的创建、查询与图搜索。"""

import json
import uuid

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    KgEntitiesRepository,
    KgRelationsRepository,
    KgSearchCacheRepository,
)
from cloud.app.services.kg_builder import get_subgraph as _get_subgraph
from cloud.app.services.kg_builder import search_kg as _search_kg
from cloud.app.services.kg_stats import dashboard_stats as _dashboard_stats
from shared.base_service import BaseService


class KgService(BaseService):
    """知识图谱服务，提供知识图谱的实体管理、关系管理与图搜索功能。"""

    def create_entity(self, data, user: dict) -> dict:
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
        entities_repo = KgEntitiesRepository(self._connection())
        return entities_repo.list_filtered(entity_type=entity_type, name=name, status_=status_)

    def get_entity(self, entity_id: str) -> dict:
        entities_repo = KgEntitiesRepository(self._connection())
        relations_repo = KgRelationsRepository(self._connection())
        row = entities_repo.get_by_entity_id(entity_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
        rels = relations_repo.list_by_entity_id(entity_id)
        return {"entity": row, "relations": rels}

    def delete_entity(self, entity_id: str) -> dict:
        entities_repo = KgEntitiesRepository(self._connection())
        if not entities_repo.exists_entity_id(entity_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
        entities_repo.soft_delete_by_entity_id(entity_id)
        return {"entity_id": entity_id, "status": "inactive"}

    def create_relation(self, data) -> dict:
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
        relations_repo = KgRelationsRepository(self._connection())
        return relations_repo.list_filtered(source=source, target=target, relation_type=relation_type)

    def delete_relation(self, relation_id: int) -> dict:
        relations_repo = KgRelationsRepository(self._connection())
        if not relations_repo.get_by_id(relation_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relation not found")
        relations_repo.delete(relation_id)
        return {"relation_id": relation_id, "deleted": True}

    def search_kg(self, data) -> dict:
        entities_repo = KgEntitiesRepository(self._connection())
        relations_repo = KgRelationsRepository(self._connection())
        cache_repo = KgSearchCacheRepository(self._connection())
        return _search_kg(entities_repo, relations_repo, cache_repo, data)

    def get_subgraph(self, entity_id: str, max_depth: int = 2) -> dict:
        entities_repo = KgEntitiesRepository(self._connection())
        relations_repo = KgRelationsRepository(self._connection())
        entity = entities_repo.get_by_entity_id(entity_id)
        if not entity or entity.get("status") != "active":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
        return _get_subgraph(entities_repo, relations_repo, entity_id, max_depth)

    def dashboard(self) -> dict:
        entities_repo = KgEntitiesRepository(self._connection())
        relations_repo = KgRelationsRepository(self._connection())
        return _dashboard_stats(entities_repo, relations_repo)
