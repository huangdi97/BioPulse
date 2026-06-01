from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from cloud.app.services.world_tree_service import WorldTreeService
from shared.auth import get_current_user
from shared.base import success

router = APIRouter(prefix="/world-tree", tags=["记忆系统"])


class NodeCreate(BaseModel):
    name: str
    description: str = ''
    parent_id: Optional[int] = None
    node_type: str = 'tag'
    sort_order: int = 0
    metadata: dict = {}


class NodeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    node_type: Optional[str] = None
    sort_order: Optional[int] = None
    metadata: Optional[dict] = None


# 1
@router.post("/nodes")
def create_node(body: NodeCreate, request=None,
                service: WorldTreeService = Depends()):
    uid = int(get_current_user(request)["sub"]) if request else 1
    row = service.create_node(
        name=body.name, description=body.description,
        parent_id=body.parent_id, node_type=body.node_type,
        sort_order=body.sort_order, metadata=body.metadata, uid=uid,
    )
    return success(data=row)


# 2
@router.get("/nodes")
def list_nodes(
    node_type: Optional[str] = Query(None),
    parent_id: Optional[int] = Query(None),
    service: WorldTreeService = Depends(),
):
    rows = service.list_nodes(node_type=node_type, parent_id=parent_id)
    return success(data=rows)


# 3
@router.get("/nodes/{node_id}")
def get_node(node_id: int, service: WorldTreeService = Depends()):
    d = service.get_node(node_id)
    return success(data=d)


# 4
@router.patch("/nodes/{node_id}")
def update_node(node_id: int, body: NodeUpdate, request=None,
                service: WorldTreeService = Depends()):
    row = service.update_node(
        node_id=node_id, name=body.name, description=body.description,
        node_type=body.node_type, sort_order=body.sort_order,
        metadata=body.metadata,
    )
    return success(data=row)


# 5
@router.delete("/nodes/{node_id}")
def delete_node(node_id: int, service: WorldTreeService = Depends()):
    message = service.delete_node(node_id)
    return success(message=message)


# 6
@router.get("/nodes/{node_id}/children")
def get_children(node_id: int, service: WorldTreeService = Depends()):
    rows = service.get_children(node_id)
    return success(data=rows)


# 7
@router.get("/nodes/{node_id}/ancestors")
def get_ancestors(node_id: int, service: WorldTreeService = Depends()):
    ancestors = service.get_ancestors(node_id)
    return success(data=ancestors)


# 8
@router.post("/nodes/{node_id}/link/{memory_id}")
def link_memory(node_id: int, memory_id: int,
                service: WorldTreeService = Depends()):
    service.link_memory(node_id, memory_id)
    return success(message="Linked")


# 9
@router.delete("/nodes/{node_id}/link/{memory_id}")
def unlink_memory(node_id: int, memory_id: int,
                  service: WorldTreeService = Depends()):
    service.unlink_memory(node_id, memory_id)
    return success(message="Unlinked")


# 10
@router.get("/nodes/{node_id}/memories")
def get_node_memories(node_id: int, service: WorldTreeService = Depends()):
    results = service.get_node_memories(node_id)
    return success(data=results)


# 11
@router.get("/tree/full")
def get_full_tree(service: WorldTreeService = Depends()):
    roots = service.get_full_tree()
    return success(data=roots)
