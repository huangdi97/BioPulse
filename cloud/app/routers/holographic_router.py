from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from cloud.app.database import get_db
from cloud.app.services.holographic_service import HolographicService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/memory", tags=["记忆系统"])


class AssociateRequest(BaseModel):
    memory_id_b: int
    relation_type: str = "related"
    weight: float = 1.0


@router.post("/{memory_id}/associate", tags=["记忆系统"])
def create_association(
    memory_id: int,
    body: AssociateRequest,
    request: Request,
    current_user=Depends(require_scope("visit")),
    db=Depends(get_db),
):
    service = HolographicService(db)
    result = service.create_association(
        memory_id_a=memory_id,
        memory_id_b=body.memory_id_b,
        relation_type=body.relation_type,
        weight=body.weight,
    )
    return success(data=result)


@router.get("/{memory_id}/holographic", tags=["记忆系统"])
def holographic_get(
    memory_id: int,
    depth: int = 3,
    db=Depends(get_db),
):
    service = HolographicService(db)
    result = service.holographic_graph(memory_id, depth)
    return success(data=result)


@router.get("/{memory_id}/associations", tags=["记忆系统"])
def get_associations(
    memory_id: int,
    limit: int = 50,
    db=Depends(get_db),
):
    service = HolographicService(db)
    result = service.get_associations(memory_id, limit)
    return success(data=result)


@router.delete("/associations/{association_id}", tags=["记忆系统"])
def delete_association(
    association_id: int,
    request: Request,
    current_user=Depends(require_scope("visit")),
    db=Depends(get_db),
):
    service = HolographicService(db)
    result = service.delete_association(association_id)
    return success(data=result)
