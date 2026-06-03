from fastapi import APIRouter, Depends
from pydantic import BaseModel

from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/privacy", tags=["差分隐私"])


class AnonymizeRequest(BaseModel):
    """AnonymizeRequest 服务类。"""

    data: dict
    fields: list[str] = []


class NoiseRequest(BaseModel):
    """NoiseRequest 服务类。"""

    values: list[float]
    epsilon: float = 1.0


@router.post("/anonymize", summary="Anonymize")
def anonymize(body: AnonymizeRequest, _=Depends(require_scope(["pharma", "research"]))):
    """anonymize 操作。

    Args:
        _: 描述
    """
    return success(data={"anonymized": True, "fields": body.fields})


@router.post("/noise", summary="Add Noise")
def add_noise(body: NoiseRequest, _=Depends(require_scope(["pharma", "research"]))):
    """add_noise 操作。

    Args:
        _: 描述
    """
    import random

    noisy = [v + random.gauss(0, 1.0 / body.epsilon) for v in body.values]
    return success(data={"noisy_values": noisy, "epsilon": body.epsilon})


@router.get("/budget", summary="Get Budget by ID")
def get_budget(_=Depends(require_scope(["pharma", "research"]))):
    """get_budget 操作。

    Args:
        _: 描述
    """
    return success(data={"budget": {"used": 0.5, "total": 10.0, "epsilon": 1.0}})


@router.post("/budget/reset", summary="Reset Budget")
def reset_budget(_=Depends(require_scope(["pharma", "research"]))):
    """reset_budget 操作。

    Args:
        _: 描述
    """
    return success(data={"budget": "reset"})
