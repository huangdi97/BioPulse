from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from shared.auth import get_current_user
from shared.base import success
from cloud.app.services.kg_service import KgService

router = APIRouter(prefix="/kg", tags=["知识图谱"])


class KgEntityCreate(BaseModel):
    entity_id: Optional[str] = None
    entity_type: str
    name: str
    aliases: list[str] = []
    properties: dict = {}
    source_table: str = ""
    source_row_id: Optional[int] = None
    confidence: float = 1.0


class KgRelationCreate(BaseModel):
    source_entity_id: str
    target_entity_id: str
    relation_type: str
    weight: float = 1.0
    properties: dict = {}
    direction: str = "directed"
    confidence: float = 1.0


class KgSearch(BaseModel):
    query: str
    entity_types: list[str] = ["hcp"]
    max_depth: int = 2
    limit: int = 20


@router.post("/entities/create")
def create_entity(data: KgEntityCreate, user: dict = Depends(get_current_user), service: KgService = Depends()):
    return success(service.create_entity(data, user))


@router.get("/entities/list")
def list_entities(
    entity_type: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    status_: str = Query("active", alias="status"),
    user: dict = Depends(get_current_user),
    service: KgService = Depends(),
):
    return success(service.list_entities(entity_type=entity_type, name=name, status_=status_))


@router.get("/entities/{entity_id}")
def get_entity(entity_id: str, user: dict = Depends(get_current_user), service: KgService = Depends()):
    return success(service.get_entity(entity_id))


@router.delete("/entities/{entity_id}")
def delete_entity(entity_id: str, user: dict = Depends(get_current_user), service: KgService = Depends()):
    return success(service.delete_entity(entity_id))


@router.post("/relations/create")
def create_relation(data: KgRelationCreate, user: dict = Depends(get_current_user), service: KgService = Depends()):
    return success(service.create_relation(data))


@router.get("/relations/list")
def list_relations(
    source: Optional[str] = Query(None),
    target: Optional[str] = Query(None),
    relation_type: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
    service: KgService = Depends(),
):
    return success(service.list_relations(source=source, target=target, relation_type=relation_type))


@router.delete("/relations/{relation_id}")
def delete_relation(relation_id: int, user: dict = Depends(get_current_user), service: KgService = Depends()):
    return success(service.delete_relation(relation_id))


@router.post("/search")
def search_kg(data: KgSearch, user: dict = Depends(get_current_user), service: KgService = Depends()):
    return success(service.search_kg(data))


@router.get("/graph/{entity_id}")
def get_subgraph(entity_id: str, max_depth: int = Query(2),
                 user: dict = Depends(get_current_user), service: KgService = Depends()):
    return success(service.get_subgraph(entity_id, max_depth))


@router.get("/dashboard")
def dashboard(user: dict = Depends(get_current_user), service: KgService = Depends()):
    return success(service.dashboard())
