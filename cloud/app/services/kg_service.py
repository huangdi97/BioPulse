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
from cloud.app.services.base import BaseService


def _bfs_expand(
    entities_repo: KgEntitiesRepository,
    relations_repo: KgRelationsRepository,
    seed_eids,
    max_depth,
):
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
    def create_entity(self, data, user: dict) -> dict:
        entities_repo = KgEntitiesRepository(self.db)
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
        entities_repo = KgEntitiesRepository(self.db)
        return entities_repo.list_filtered(entity_type=entity_type, name=name, status_=status_)

    def get_entity(self, entity_id: str) -> dict:
        entities_repo = KgEntitiesRepository(self.db)
        relations_repo = KgRelationsRepository(self.db)
        row = entities_repo.get_by_entity_id(entity_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
        rels = relations_repo.list_by_entity_id(entity_id)
        return {"entity": row, "relations": rels}

    def delete_entity(self, entity_id: str) -> dict:
        entities_repo = KgEntitiesRepository(self.db)
        if not entities_repo.exists_entity_id(entity_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
        entities_repo.soft_delete_by_entity_id(entity_id)
        return {"entity_id": entity_id, "status": "inactive"}

    def create_relation(self, data) -> dict:
        entities_repo = KgEntitiesRepository(self.db)
        relations_repo = KgRelationsRepository(self.db)
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
        relations_repo = KgRelationsRepository(self.db)
        return relations_repo.list_filtered(source=source, target=target, relation_type=relation_type)

    def delete_relation(self, relation_id: int) -> dict:
        relations_repo = KgRelationsRepository(self.db)
        if not relations_repo.get_by_id(relation_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relation not found")
        relations_repo.delete(relation_id)
        return {"relation_id": relation_id, "deleted": True}

    def search_kg(self, data) -> dict:
        entities_repo = KgEntitiesRepository(self.db)
        relations_repo = KgRelationsRepository(self.db)
        cache_repo = KgSearchCacheRepository(self.db)
        seeds = [
            r["entity_id"]
            for r in entities_repo.search_by_name_and_types(
                data.query, entity_types=data.entity_types, limit=data.limit
            )
        ]
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
        entities_repo = KgEntitiesRepository(self.db)
        relations_repo = KgRelationsRepository(self.db)
        entity = entities_repo.get_by_entity_id(entity_id)
        if not entity or entity.get("status") != "active":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
        ent_dict, rel_dict = _bfs_expand(entities_repo, relations_repo, [entity_id], max_depth)
        return {
            "entities": list(ent_dict.values()),
            "relations": list(rel_dict.values()),
        }

    def dashboard(self) -> dict:
        entities_repo = KgEntitiesRepository(self.db)
        relations_repo = KgRelationsRepository(self.db)
        return {
            "total_entities": entities_repo.count_active(),
            "total_relations": relations_repo.count_all(),
            "entity_types": entities_repo.count_by_entity_type(),
            "relation_types": relations_repo.count_by_relation_type(),
            "top_connected": relations_repo.top_connected(limit=10),
        }
